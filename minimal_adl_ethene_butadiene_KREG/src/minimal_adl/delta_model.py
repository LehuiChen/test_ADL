from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from .io_utils import write_csv_rows, write_json
from .mlatom_bridge import import_mlatom

ml = import_mlatom()


class DeltaMLModel(ml.al_utils.ml_model):
    """涓绘ā鍨嬪拰杈呭姪妯″瀷鐨勬渶灏忓皝瑁呫€?""

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
        """鏍规嵁宸ヤ綔鐩綍鐢熸垚涓绘ā鍨嬪拰杈呭姪妯″瀷鏂囦欢璺緞銆?""

        workdir = Path(workdir)
        extension = self._model_extension()
        self.main_model_file = str((workdir / f"{self.main_model_stem}{extension}").resolve())
        self.aux_model_file = str((workdir / f"{self.aux_model_stem}{extension}").resolve())
        return self.main_model_file, self.aux_model_file

    def load_trained_models(self, workdir: str | Path, *, load_main: bool = True, load_aux: bool = True) -> None:
        """浠庣鐩樿鍙栧凡缁忚缁冨ソ鐨勬ā鍨嬫枃浠躲€?""

        self.prepare_model_paths(workdir)
        if load_main:
            if not os.path.exists(self.main_model_file):
                raise FileNotFoundError(f"鎵句笉鍒颁富妯″瀷鏂囦欢锛歿self.main_model_file}")
            self.main_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.main_model_file,
                device=self.device,
                verbose=self.verbose,
            )
        if load_aux:
            if not os.path.exists(self.aux_model_file):
                raise FileNotFoundError(f"鎵句笉鍒拌緟鍔╂ā鍨嬫枃浠讹細{self.aux_model_file}")
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
        """璁粌涓绘ā鍨嬪拰杈呭姪妯″瀷銆?""

        if molecular_database is None:
            raise ValueError("璁粌鍓嶅繀椤绘彁渚?molecular_database銆?)

        if self.ml_model_type.casefold() == "nequip":
            raise NotImplementedError(
                "NequIP backend is reserved but not implemented yet in this project. "
                "Please first complete a NequIP adapter in DeltaMLModel.initialize_model/model_trainer/predict "
                "or switch ml_model_type to ANI or MACE."
            )
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
        elif not train_main and os.path.exists(self.aux_model_file):
            self.aux_model = self.initialize_model(
                ml_model_type=self.ml_model_type,
                model_file=self.aux_model_file,
                device=self.device,
                verbose=self.verbose,
            )
        else:
            self.aux_model = None

        if "uq_threshold" in al_info:
            self.uq_threshold = float(al_info["uq_threshold"])
        elif self.main_model is not None and self.aux_model is not None:
            valdb_copy = valdb.copy()
            self.predict(molecular_database=valdb_copy)
            uq_values = [float(molecule.uq) for molecule in valdb_copy]
            self.uq_threshold = float(self.threshold_metric(uq_values, metric=al_info.get("threshold_metric", "m+3mad")))
        else:
            self.uq_threshold = None

        summary, summary_details = self.summary(subtraindb=subtraindb, valdb=valdb, include_details=True)
        artifact_paths = self.write_training_artifacts(
            workdir=workdir,
            summary=summary,
            summary_details=summary_details,
        )
        state = {
            "main_model_file": self.main_model_file if self.main_model is not None else None,
            "aux_model_file": self.aux_model_file if self.aux_model is not None else None,
            "uq_threshold": self.uq_threshold,
            "train_main": train_main,
            "train_aux": train_aux,
            **artifact_paths,
        }
        write_json(workdir / summary_filename, summary)
        write_json(workdir / state_filename, state)
        return state

    def predict(self, molecule=None, molecular_database=None, **kwargs) -> None:  # noqa: ARG002
        """瀵逛竴涓垎瀛愭垨鍒嗗瓙鏁版嵁搴撳仛棰勬祴锛屽苟璁＄畻涓嶇‘瀹氭€с€?""

        if molecule is not None:
            molecular_database = ml.data.molecular_database(molecule)
        elif molecular_database is None:
            raise ValueError("predict 闇€瑕?molecule 鎴?molecular_database銆?)

        if self.main_model is None:
            raise RuntimeError("涓绘ā鍨嬪皻鏈垵濮嬪寲锛屾棤娉曢娴嬨€?)
        if self.baseline is None:
            raise RuntimeError("baseline 鏂规硶鏈缃紝鏃犳硶鎭㈠鎬昏兘閲忓拰鎬诲姏銆?)

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
        """鎸夌収 MLatom 妯″瀷绫诲瀷璁粌妯″瀷銆?""

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
                raise ValueError(f"褰撳墠鏈疄鐜扮殑涓绘ā鍨嬬被鍨嬶細{ml_model_type}")
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
                raise ValueError(f"褰撳墠鏈疄鐜扮殑杈呭姪妯″瀷绫诲瀷锛歿ml_model_type}")

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            return float(value)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _safe_vector_property(molecule: Any, property_name: str) -> np.ndarray | None:
        try:
            return np.asarray(molecule.get_xyz_vectorial_properties(property_name), dtype=float)
        except Exception:  # noqa: BLE001
            pass

        raw_value = getattr(molecule, property_name, None)
        if raw_value is None:
            return None
        try:
            return np.asarray(raw_value, dtype=float)
        except Exception:  # noqa: BLE001
            return None

    def _normalize_history_payload(self, payload: Any) -> dict[str, list[float]]:
        if isinstance(payload, dict):
            normalized: dict[str, list[float]] = {}
            for key, value in payload.items():
                if isinstance(value, dict) and "history" in value:
                    nested = self._normalize_history_payload(value["history"])
                    if nested:
                        return nested
                    continue
                try:
                    series = [float(item) for item in np.ravel(value).tolist()]
                except Exception:  # noqa: BLE001
                    continue
                if series:
                    normalized[str(key)] = series
            return normalized

        if hasattr(payload, "history") and isinstance(payload.history, dict):
            return self._normalize_history_payload(payload.history)

        if isinstance(payload, (list, tuple)) and payload and all(isinstance(item, dict) for item in payload):
            normalized = {}
            keys = {key for item in payload for key in item.keys()}
            for key in keys:
                try:
                    series = [float(item[key]) for item in payload if key in item]
                except Exception:  # noqa: BLE001
                    continue
                if series:
                    normalized[str(key)] = series
            return normalized

        return {}

    def _extract_model_history(self, model: Any, model_key: str) -> dict[str, Any]:
        if model is None:
            return {
                "available": False,
                "model": model_key,
                "reason": "褰撳墠娌℃湁鍙敤鐨勬ā鍨嬪璞★紝鍥犳鏃犳硶瀵煎嚭璁粌 history銆?,
            }

        candidate_attrs = [
            "history",
            "training_history",
            "history_",
            "_history",
            "learning_curve",
            "learning_curve_",
            "metrics_history",
        ]
        for attr_name in candidate_attrs:
            if not hasattr(model, attr_name):
                continue
            payload = getattr(model, attr_name)
            normalized = self._normalize_history_payload(payload)
            if normalized:
                return {
                    "available": True,
                    "model": model_key,
                    "source_attribute": attr_name,
                    "history": normalized,
                }

        return {
            "available": False,
            "model": model_key,
            "reason": "褰撳墠 ANI/MLatom 鎺ュ彛娌℃湁鏆撮湶缁撴瀯鍖栭€?epoch history锛屽洜姝よ繖閲屽彧淇濈暀鏈€缁堟寚鏍囧拰閫愭牱鏈娴嬨€?,
        }

    def _artifact_paths(self, workdir: Path) -> dict[str, Path]:
        return {
            "training_split_file": workdir / "training_split.json",
            "train_main_predictions_file": workdir / "train_main_predictions.csv",
            "train_aux_predictions_file": workdir / "train_aux_predictions.csv",
            "train_main_history_file": workdir / "train_main_history.json",
            "train_aux_history_file": workdir / "train_aux_history.json",
        }

    def _build_prediction_rows(
        self,
        *,
        trainingdb_ref,
        trainingdb,
        split_labels: list[str],
        model_key: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        prediction_attr = "delta_energy" if model_key == "main_model" else "aux_delta_energy"

        for index, (ref_molecule, pred_molecule, split_label) in enumerate(zip(trainingdb_ref, trainingdb, split_labels)):
            sample_id = str(getattr(ref_molecule, "id", f"sample_{index:04d}"))
            y_true = self._safe_float(getattr(ref_molecule, "delta_energy", None))
            y_pred = self._safe_float(getattr(pred_molecule, prediction_attr, None))
            residual = None if y_true is None or y_pred is None else y_pred - y_true

            row: dict[str, Any] = {
                "sample_id": sample_id,
                "split": split_label,
                "y_true": y_true,
                "y_pred": y_pred,
                "residual": residual,
                "abs_error": None if residual is None else abs(residual),
                "baseline_energy": self._safe_float(getattr(ref_molecule, "baseline_energy", None)),
                "target_energy": self._safe_float(getattr(ref_molecule, "reference_energy", None)),
                "predicted_total_energy": self._safe_float(getattr(pred_molecule, "energy", None)),
                "uncertainty": self._safe_float(getattr(pred_molecule, "uq", None)),
            }

            if model_key == "main_model":
                true_grad = self._safe_vector_property(ref_molecule, "delta_energy_gradients")
                pred_grad = self._safe_vector_property(pred_molecule, "delta_energy_gradients")
                if true_grad is not None:
                    true_force = -true_grad
                    row["true_gradient_norm"] = float(np.linalg.norm(true_grad))
                    row["true_force_norm"] = float(np.linalg.norm(true_force))
                if pred_grad is not None:
                    pred_force = -pred_grad
                    row["pred_gradient_norm"] = float(np.linalg.norm(pred_grad))
                    row["pred_force_norm"] = float(np.linalg.norm(pred_force))
                if true_grad is not None and pred_grad is not None:
                    grad_diff = pred_grad - true_grad
                    force_diff = (-pred_grad) - (-true_grad)
                    row["gradient_rmse"] = float(np.sqrt(np.mean(np.square(grad_diff))))
                    row["force_error_norm"] = float(np.linalg.norm(force_diff))
            else:
                row["predicted_delta_energy_main"] = self._safe_float(getattr(pred_molecule, "delta_energy", None))
                if row["baseline_energy"] is not None and y_pred is not None:
                    row["predicted_total_energy"] = row["baseline_energy"] + y_pred

            rows.append(row)

        return rows

    def write_training_artifacts(
        self,
        *,
        workdir: Path,
        summary: dict[str, Any],
        summary_details: dict[str, Any],
    ) -> dict[str, str]:
        artifact_paths = self._artifact_paths(workdir)
        split_rows = summary_details.get("split_rows", [])
        write_json(
            artifact_paths["training_split_file"],
            {
                "num_subtrain": summary.get("num_subtrain", 0),
                "num_validation": summary.get("num_validation", 0),
                "subtrain_sample_ids": [item["sample_id"] for item in split_rows if item["split"] == "subtrain"],
                "validation_sample_ids": [item["sample_id"] for item in split_rows if item["split"] == "validation"],
                "rows": split_rows,
            },
        )

        main_rows = summary_details.get("main_prediction_rows", [])
        aux_rows = summary_details.get("aux_prediction_rows", [])
        write_csv_rows(
            artifact_paths["train_main_predictions_file"],
            main_rows,
            fieldnames=[
                "sample_id",
                "split",
                "y_true",
                "y_pred",
                "residual",
                "abs_error",
                "baseline_energy",
                "target_energy",
                "predicted_total_energy",
                "uncertainty",
                "true_gradient_norm",
                "pred_gradient_norm",
                "gradient_rmse",
                "true_force_norm",
                "pred_force_norm",
                "force_error_norm",
            ],
        )
        write_csv_rows(
            artifact_paths["train_aux_predictions_file"],
            aux_rows,
            fieldnames=[
                "sample_id",
                "split",
                "y_true",
                "y_pred",
                "residual",
                "abs_error",
                "baseline_energy",
                "target_energy",
                "predicted_total_energy",
                "uncertainty",
                "predicted_delta_energy_main",
            ],
        )

        main_history = self._extract_model_history(self.main_model, "main_model")
        aux_history = self._extract_model_history(self.aux_model, "aux_model")
        if "main_model" in summary:
            main_history["final_metrics"] = summary["main_model"]
        if "aux_model" in summary:
            aux_history["final_metrics"] = summary["aux_model"]
        write_json(artifact_paths["train_main_history_file"], main_history)
        write_json(artifact_paths["train_aux_history_file"], aux_history)

        return {key: str(path.resolve()) for key, path in artifact_paths.items()}

    def summary(self, *, subtraindb, valdb, include_details: bool = False):
        """杈撳嚭璁粌鎽樿锛屽苟鍦ㄩ渶瑕佹椂杩斿洖閫愭牱鏈瘖鏂粏鑺傘€?""

        summary = {
            "num_subtrain": len(subtraindb),
            "num_validation": len(valdb),
            "uq_threshold": self.uq_threshold,
        }

        if self.main_model is None:
            if include_details:
                return summary, {"split_rows": [], "main_prediction_rows": [], "aux_prediction_rows": []}
            return summary

        trainingdb_ref = subtraindb + valdb
        trainingdb = trainingdb_ref.copy()
        self.predict(molecular_database=trainingdb)

        n_subtrain = len(subtraindb)
        split_labels = ["subtrain"] * n_subtrain + ["validation"] * len(valdb)
        split_rows = [
            {
                "sample_id": str(getattr(molecule, "id", f"sample_{index:04d}")),
                "split": split_labels[index],
            }
            for index, molecule in enumerate(trainingdb_ref)
        ]
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

        if not include_details:
            return summary

        return summary, {
            "split_rows": split_rows,
            "main_prediction_rows": self._build_prediction_rows(
                trainingdb_ref=trainingdb_ref,
                trainingdb=trainingdb,
                split_labels=split_labels,
                model_key="main_model",
            ),
            "aux_prediction_rows": self._build_prediction_rows(
                trainingdb_ref=trainingdb_ref,
                trainingdb=trainingdb,
                split_labels=split_labels,
                model_key="aux_model",
            )
            if self.aux_model is not None
            else [],
        }

