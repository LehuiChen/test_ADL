from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .io_utils import write_json
from .mlatom_bridge import import_mlatom

ml = import_mlatom()


class DeltaMLModel(ml.al_utils.ml_model):
    """主模型和辅助模型的最小封装。"""

    def __init__(
        self,
        *,
        al_info: dict[str, Any] | None = None,
        model_file: str | None = None,
        device: str | None = None,
        verbose: bool = False,
        ml_model_type: str = "ANI",
        baseline=None,
        validation_set_fraction: float = 0.1,
        main_model_stem: str = "delta_main_model",
        aux_model_stem: str = "delta_aux_model",
        **kwargs,
    ):
        super().__init__(
            al_info=al_info or {},
            model_file=model_file,
            device=device,
            verbose=verbose,
            ml_model_type=ml_model_type,
            **kwargs,
        )
        self.baseline = baseline
        self.validation_set_fraction = validation_set_fraction
        self.main_model_stem = main_model_stem
        self.aux_model_stem = aux_model_stem
        self.uq_threshold = None
        self.main_model = getattr(self, "main_model", None)
        self.aux_model = getattr(self, "aux_model", None)

    def _model_extension(self) -> str:
        return ".npz" if self.ml_model_type.casefold() == "kreg" else ".pt"

    def prepare_model_paths(self, workdir: str | Path) -> tuple[str, str]:
        """根据工作目录生成主模型和辅助模型文件路径。"""

        workdir = Path(workdir)
        extension = self._model_extension()
        self.main_model_file = str((workdir / f"{self.main_model_stem}{extension}").resolve())
        self.aux_model_file = str((workdir / f"{self.aux_model_stem}{extension}").resolve())
        return self.main_model_file, self.aux_model_file

    def load_trained_models(self, workdir: str | Path, *, load_main: bool = True, load_aux: bool = True) -> None:
        """从磁盘读取已经训练好的模型文件。"""

        self.prepare_model_paths(workdir)
        if load_main:
            if not os.path.exists(self.main_model_file):
                raise FileNotFoundError(f"找不到主模型文件：{self.main_model_file}")
            self.main_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.main_model_file,
                device=self.device,
                verbose=self.verbose,
            )
        if load_aux:
            if not os.path.exists(self.aux_model_file):
                raise FileNotFoundError(f"找不到辅助模型文件：{self.aux_model_file}")
            self.aux_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.aux_model_file,
                device=self.device,
                verbose=self.verbose,
            )

    def train(
        self,
        *,
        molecular_database=None,
        al_info: dict[str, Any] | None = None,
        train_main: bool = True,
        train_aux: bool = True,
        summary_filename: str = "training_summary.json",
        state_filename: str = "training_state.json",
    ) -> dict[str, Any]:
        """训练主模型和辅助模型。"""

        if molecular_database is None:
            raise ValueError("训练前必须提供 molecular_database。")

        al_info = dict(al_info or {})
        workdir = Path(al_info.get("working_directory", ".")).resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        self.prepare_model_paths(workdir)

        [subtraindb, valdb] = molecular_database.split(
            number_of_splits=2,
            fraction_of_points_in_splits=[1 - self.validation_set_fraction, self.validation_set_fraction],
            sampling="random",
        )

        if train_main:
            self.main_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.main_model_file,
                device=self.device,
                verbose=self.verbose,
            )
            self.model_trainer(
                ml_model_type=self.ml_model_type,
                model=self.main_model,
                subtraindb=subtraindb,
                valdb=valdb,
                learning_grad=True,
            )
        elif os.path.exists(self.main_model_file):
            self.main_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.main_model_file,
                device=self.device,
                verbose=self.verbose,
            )

        if train_aux:
            self.aux_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.aux_model_file,
                device=self.device,
                verbose=self.verbose,
            )
            self.model_trainer(
                ml_model_type=self.ml_model_type,
                model=self.aux_model,
                subtraindb=subtraindb,
                valdb=valdb,
                learning_grad=False,
            )
        elif os.path.exists(self.aux_model_file):
            self.aux_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.aux_model_file,
                device=self.device,
                verbose=self.verbose,
            )

        if "uq_threshold" in al_info:
            self.uq_threshold = float(al_info["uq_threshold"])
        elif self.main_model is not None and self.aux_model is not None:
            valdb_copy = valdb.copy()
            self.predict(molecular_database=valdb_copy)
            uq_values = [float(molecule.uq) for molecule in valdb_copy]
            self.uq_threshold = float(self.threshold_metric(uq_values, metric=al_info.get("threshold_metric", "m+3mad")))
        else:
            self.uq_threshold = None

        summary = self.summary(subtraindb=subtraindb, valdb=valdb)
        state = {
            "main_model_file": self.main_model_file if self.main_model is not None else None,
            "aux_model_file": self.aux_model_file if self.aux_model is not None else None,
            "uq_threshold": self.uq_threshold,
            "train_main": train_main,
            "train_aux": train_aux,
        }
        write_json(workdir / summary_filename, summary)
        write_json(workdir / state_filename, state)
        return state

    def predict(self, molecule=None, molecular_database=None, **kwargs) -> None:  # noqa: ARG002
        """对一个分子或分子数据库做预测，并计算不确定性。"""

        if molecule is not None:
            molecular_database = ml.data.molecular_database(molecule)
        elif molecular_database is None:
            raise ValueError("predict 需要 molecule 或 molecular_database。")

        if self.main_model is None:
            raise RuntimeError("主模型尚未初始化，无法预测。")
        if self.baseline is None:
            raise RuntimeError("baseline 方法未设置，无法恢复总能量和总力。")

        self.main_model.predict(
            molecular_database=molecular_database,
            property_to_predict="delta_energy",
            xyz_derivative_property_to_predict="delta_energy_gradients",
        )

        baseline_copy = molecular_database.copy(atomic_labels=["xyz_coordinates"])
        self.baseline.predict(
            molecular_database=baseline_copy,
            calculate_energy=True,
            calculate_energy_gradients=True,
        )

        for index, molecule_item in enumerate(molecular_database):
            molecule_item.energy = molecule_item.delta_energy + baseline_copy[index].energy
            molecule_item.add_xyz_vectorial_property(
                molecule_item.get_xyz_vectorial_properties("delta_energy_gradients")
                + baseline_copy[index].get_xyz_vectorial_properties("energy_gradients"),
                "energy_gradients",
            )

        if self.aux_model is not None:
            self.aux_model.predict(
                molecular_database=molecular_database,
                property_to_predict="aux_delta_energy",
            )
            for molecule_item in molecular_database:
                molecule_item.uq = abs(float(molecule_item.delta_energy) - float(molecule_item.aux_delta_energy))
                molecule_item.uncertain = self.uq_threshold is not None and molecule_item.uq > self.uq_threshold

    def model_trainer(self, ml_model_type, model, subtraindb, valdb, learning_grad=False) -> None:
        """按照 MLatom 模型类型训练模型。"""

        subtraindb_copy = subtraindb.copy()
        valdb_copy = valdb.copy()

        if ml_model_type.casefold() == "kreg":
            for molecule in subtraindb_copy + valdb_copy:
                molecule.energy = molecule.reference_energy

        if learning_grad:
            if ml_model_type.casefold() == "ani":
                model.train(
                    molecular_database=subtraindb_copy,
                    validation_molecular_database=valdb_copy,
                    property_to_learn="delta_energy",
                    xyz_derivative_property_to_learn="delta_energy_gradients",
                )
            elif ml_model_type.casefold() == "kreg":
                saved_path = model.model_file
                model.model_file = "mlmodel.npz"
                model.hyperparameters["sigma"].minval = 2 ** -5
                model.optimize_hyperparameters(
                    subtraining_molecular_database=subtraindb_copy,
                    validation_molecular_database=valdb_copy,
                    optimization_algorithm="grid",
                    hyperparameters=["lambda", "sigma"],
                    training_kwargs={
                        "property_to_learn": "delta_energy",
                        "xyz_derivative_property_to_learn": "delta_energy_gradients",
                        "prior": "mean",
                    },
                    prediction_kwargs={
                        "property_to_predict": "estimated_delta_energy",
                        "xyz_derivative_property_to_predict": "estimated_delta_energy_gradients",
                    },
                )
                model.model_file = saved_path
                model.kreg_api.save_model(model.model_file)
            elif ml_model_type.casefold() == "mace":
                model.train(
                    molecular_database=subtraindb_copy,
                    validation_molecular_database=valdb_copy,
                    property_to_learn="delta_energy",
                    xyz_derivative_property_to_learn="delta_energy_gradients",
                )
            else:
                raise ValueError(f"当前未实现的主模型类型：{ml_model_type}")
        else:
            if ml_model_type.casefold() == "ani":
                model.train(
                    molecular_database=subtraindb_copy,
                    validation_molecular_database=valdb_copy,
                    property_to_learn="delta_energy",
                )
            elif ml_model_type.casefold() == "kreg":
                saved_path = model.model_file
                model.model_file = "mlmodel.npz"
                model.hyperparameters["sigma"].minval = 2 ** -5
                model.optimize_hyperparameters(
                    subtraining_molecular_database=subtraindb_copy,
                    validation_molecular_database=valdb_copy,
                    optimization_algorithm="grid",
                    hyperparameters=["lambda", "sigma"],
                    training_kwargs={"property_to_learn": "delta_energy", "prior": "mean"},
                    prediction_kwargs={"property_to_predict": "estimated_energy"},
                )
                model.model_file = saved_path
                model.kreg_api.save_model(model.model_file)
            elif ml_model_type.casefold() == "mace":
                model.train(
                    molecular_database=subtraindb_copy,
                    validation_molecular_database=valdb_copy,
                    property_to_learn="delta_energy",
                )
            else:
                raise ValueError(f"当前未实现的辅助模型类型：{ml_model_type}")

    def summary(self, *, subtraindb, valdb) -> dict[str, Any]:
        """输出训练摘要，不画图，只保存数字指标。"""

        summary = {
            "num_subtrain": len(subtraindb),
            "num_validation": len(valdb),
            "uq_threshold": self.uq_threshold,
        }

        if self.main_model is None:
            return summary

        trainingdb_ref = subtraindb + valdb
        trainingdb = trainingdb_ref.copy()
        self.predict(molecular_database=trainingdb)

        n_subtrain = len(subtraindb)
        values = trainingdb_ref.get_properties("delta_energy")
        predicted_values = trainingdb.get_properties("delta_energy")
        gradients = trainingdb_ref.get_xyz_vectorial_properties("delta_energy_gradients")
        predicted_gradients = trainingdb.get_xyz_vectorial_properties("delta_energy_gradients")

        summary["main_model"] = {
            "subtrain_energy_rmse": float(ml.stats.rmse(predicted_values[:n_subtrain], values[:n_subtrain])),
            "validation_energy_rmse": float(ml.stats.rmse(predicted_values[n_subtrain:], values[n_subtrain:])),
            "subtrain_energy_pcc": float(ml.stats.correlation_coefficient(predicted_values[:n_subtrain], values[:n_subtrain])),
            "validation_energy_pcc": float(
                ml.stats.correlation_coefficient(predicted_values[n_subtrain:], values[n_subtrain:])
            ),
            "subtrain_gradient_rmse": float(
                ml.stats.rmse(predicted_gradients[:n_subtrain].flatten(), gradients[:n_subtrain].flatten())
            ),
            "validation_gradient_rmse": float(
                ml.stats.rmse(predicted_gradients[n_subtrain:].flatten(), gradients[n_subtrain:].flatten())
            ),
        }

        if self.aux_model is not None:
            aux_values = trainingdb.get_properties("aux_delta_energy")
            summary["aux_model"] = {
                "subtrain_energy_rmse": float(ml.stats.rmse(aux_values[:n_subtrain], values[:n_subtrain])),
                "validation_energy_rmse": float(ml.stats.rmse(aux_values[n_subtrain:], values[n_subtrain:])),
                "subtrain_energy_pcc": float(ml.stats.correlation_coefficient(aux_values[:n_subtrain], values[:n_subtrain])),
                "validation_energy_pcc": float(
                    ml.stats.correlation_coefficient(aux_values[n_subtrain:], values[n_subtrain:])
                ),
            }

        return summary

