# AIQM 闆嗙兢绗竴杞繍琛屾墜鍐?

杩欎唤鎵嬪唽瀵瑰簲褰撳墠浠撳簱涓殑鎺ㄨ崘涓荤嚎锛?

- 椤圭洰鐩綍锛歚minimal_adl_ethene_butadiene/`
- 浣撶郴锛歚ethene + 1,3-butadiene`
- `baseline`锛歚GFN2-xTB`
- `target`锛欸aussian `wB97X-D/6-31G*`
- 涓绘ā鍨嬶細`ANI`
- 榛樿璁粌鐜鍚嶏細`ADL_env`

褰撳墠鏈€鎺ㄨ崘鐨勬柟寮忎笉鏄墜宸ラ€愭潯鏁插畬鏁撮樁娈靛懡浠わ紝鑰屾槸锛?

1. 鍏堝畬鎴愮幆澧冭嚜妫€
2. 鍐嶈繍琛?`run_first_round_pipeline.py`
3. 璺戝畬鐩存帴鎵撳紑 `docs/DATA_ANALYSIS.ipynb`
4. notebook 浼氳嚜鍔ㄨ瘑鍒渶鏂拌疆娆★紝骞舵眹鎬绘墍鏈夊凡瀛樺湪杞鐨勯€夌偣鍘嗗彶

---

## 0. 杩涘叆椤圭洰鐩綍

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
pwd
```

---

## 1. 璁粌涓绘祦绋嬩娇鐢?`ADL_env`

璁粌銆佹爣娉ㄣ€乁Q 鍜屼富鎺ц剼鏈兘榛樿璧?`ADL_env`銆傚厛杩涘叆璁粌鐜锛?

```bash
source ~/.bashrc
conda activate ADL_env
```

---

## 2. 濡傛灉鍙仛鍒嗘瀽锛屽啀鍑嗗 `data_env`

`docs/DATA_ANALYSIS.ipynb` 鐨勭粯鍥惧拰琛ㄦ牸鍒嗘瀽鎺ㄨ崘鏀惧湪 `data_env`銆傚鏋滆繖涓幆澧冮噷杩樻病鏈夌粯鍥惧簱锛屽彲浠ュ厛琛ユ渶甯哥己鐨?`seaborn`锛?
```bash
source ~/.bashrc
conda activate data_env
python -m pip install "seaborn>=0.12"
```

濡傛灉 `data_env` 閲岃繕缂?`pandas`銆乣matplotlib` 鎴?`scikit-learn`锛屽啀鎸夋姤閿欒ˉ瑁呭嵆鍙€傝繖鏍?notebook 鍦ㄦ湇鍔″櫒涓婂氨涓嶄細鍐嶅洜涓虹己 `seaborn` 鑰岀洿鎺ユ姤閿欍€?
濡傛灉浣犳槸閫氳繃 VS Code Remote 鎴栧叾浠栬繙绋?notebook 鏂瑰紡鎵撳紑鏂囦欢锛屼笖 notebook 閲屸€滀粨搴撴爣鍑嗘枃浠垛€濅竴鍒楀叏閮ㄦ樉绀?`False`锛岄€氬父涓嶆槸璁粌娌′骇鍑猴紝鑰屾槸 notebook 鎶婇」鐩牴鐩綍璇嗗埆閿欎簡銆傚綋鍓嶇増鏈凡缁忓寮轰簡鑷姩璇嗗埆閫昏緫锛涘鏋滀粛鐒惰鍒わ紝鍙互鍦?`docs/DATA_ANALYSIS.ipynb` 鐨勯厤缃尯鐩存帴璁剧疆 `PROJECT_ROOT_OVERRIDE = Path("/share/home/Chenlehui/work/test_ADL")`銆?
---

## 3. 鍔犺浇绯荤粺绋嬪簭璺緞

```bash
source /share/apps/gaussian/g16-env.sh
source /share/env/ips2018u1.env
source ~/.bashrc
conda activate ADL_env
export PATH=/share/apps/gaussian/g16:/share/pubbin:/share/home/Chenlehui/bin:/share/apps/xtb-6.7.1/xtb-dist/bin:$PATH
export dftd4bin=/share/apps/dftd4-3.5.0/bin/dftd4
```

鍩虹妫€鏌ワ細

```bash
which python
python --version
which xtb
xtb --version
which g16
```

---

## 4. 鍏堝仛鐜鑷

```bash
conda activate ADL_env
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

濡傛灉浣犲凡缁忚繘鍏?GPU 鑺傜偣锛屽啀缁х画锛?

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
```

鑷鎶ュ憡浼氬啓鍒帮細

- `results/check_environment_latest.json`

---

## 5. 涓€閿窇瀹屾暣绗竴杞?

鎺ㄨ崘鍛戒护锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

濡傛灉浣犳槸绗竴娆″湪褰撳墠鏈烘埧璺戯紝寤鸿鍏堟彃鍏?smoke test锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs       --with-smoke-tests
```

杩欎釜涓绘帶鑴氭湰浼氶『搴忔墽琛岋細

1. `check_environment`
2. `sample_initial_geometries`
3. `initial_selection`
4. `run_xtb_labels`
5. `run_target_labels`
6. `build_delta_dataset`
7. `train_main_model`
8. `train_aux_model`
9. `export_training_diagnostics`
10. `evaluate_uncertainty`
11. `select_round_001`

闃舵鐘舵€佷細鍐欏埌锛?

- `results/pipeline_run_summary.json`

---

## 6. 濡備綍鎭㈠鎵ц

`run_first_round_pipeline.py` 榛樿鍚敤 `resume`锛屽鏋滄爣鍑嗕骇鐗╁凡瀛樺湪锛屼細鑷姩璺宠繃宸插畬鎴愰樁娈点€?

甯歌鐢ㄦ硶锛?

浠庤缁冮樁娈电户缁線鍚庤窇锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --submit-mode-train pbs       --submit-mode-uq pbs
```

寮哄埗閲嶈窇璁粌鍙婁箣鍚庨樁娈碉細

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --force       --submit-mode-train pbs       --submit-mode-uq pbs
```

鍙兂璺戝埌璇婃柇浜х墿瀵煎嚭涓烘锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --to-stage export_training_diagnostics       --submit-mode-labels pbs       --submit-mode-train pbs
```

---

## 7. 濡傛灉浣犱粛鐒堕渶瑕佸崟闃舵鍛戒护
涓绘帶鑴氭湰涓嶄細搴熷純鍘熸湁鑴氭湰銆傚鏋滀綘瑕佹帓閿欙紝浠嶇劧鍙互鍗曠嫭杩愯锛?

```bash
python scripts/sample_initial_geometries.py --config configs/base.yaml

python scripts/active_learning_loop.py       --config configs/base.yaml       --manifest data/raw/geometry_pool_manifest.json       --mode initial-selection       --round-index 0

python scripts/run_xtb_labels.py       --config configs/base.yaml       --manifest data/raw/initial_selection_manifest.json       --submit-mode pbs

python scripts/run_target_labels.py       --config configs/base.yaml       --manifest data/raw/initial_selection_manifest.json       --submit-mode pbs

python scripts/build_delta_dataset.py       --config configs/base.yaml       --manifest data/raw/initial_selection_manifest.json

python scripts/train_main_model.py       --config configs/base.yaml       --submit-mode pbs

python scripts/train_aux_model.py       --config configs/base.yaml       --submit-mode pbs

python scripts/export_training_diagnostics.py       --config configs/base.yaml

python scripts/evaluate_uncertainty.py       --config configs/base.yaml       --manifest data/raw/geometry_pool_manifest.json       --submit-mode pbs

python scripts/active_learning_loop.py       --config configs/base.yaml       --manifest data/raw/geometry_pool_manifest.json       --mode next-round       --uncertainty results/uncertainty_latest.json       --round-index 1
```

---

## 8. 璺戝畬浠ュ悗璇ユ鏌ュ摢浜涙枃浠?

璁粌鐩稿叧锛?

- `models/training_summary.json`
- `models/training_state.json`
- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`

缁撴灉鐩稿叧锛?

- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/round_001_selected_manifest.json`
- `results/pipeline_run_summary.json`

蹇€熸鏌ワ細

```bash
ls models
ls results
cat results/pipeline_run_summary.json
cat models/training_diagnostics.json
```

---

## 9. 濡備綍鎵撳紑鍒嗘瀽 notebook

璺戝畬浠ュ悗鐩存帴鎵撳紑锛?

- `docs/DATA_ANALYSIS.ipynb`

濡傛灉鏈嶅姟鍣ㄤ笂宸茬粡鏈?Jupyter锛?

```bash
cd /share/home/Chenlehui/work/test_ADL
conda activate data_env
jupyter lab
```

鏍囧噯璺緞涓嬶紝杩欎釜 notebook 榛樿浼氫紭鍏堣鍙栵細

- `minimal_adl_ethene_butadiene/models/train_main_history.json`
- `minimal_adl_ethene_butadiene/models/train_main_predictions.csv`
- `minimal_adl_ethene_butadiene/models/training_summary.json`
- `minimal_adl_ethene_butadiene/results/uncertainty_latest.json`
- `minimal_adl_ethene_butadiene/results/round_001_selection_summary.json`

濡傛灉杩欎簺鏂囦欢閮藉湪鏍囧噯浣嶇疆锛岄€氬父涓嶉渶瑕佸厛鏀?`CONFIG`銆?

---

## 10. 甯歌鎺掗敊鍛戒护

鏌ョ湅涓绘帶娴佺▼鐘舵€侊細

```bash
cat results/pipeline_run_summary.json
```

鏌ョ湅鏈€杩戣缁冪姸鎬侊細

```bash
cat models/train_main_status.json
cat models/train_aux_status.json
```

鏌ョ湅鏈€杩?UQ 鐘舵€侊細

```bash
cat results/uncertainty_status.json
```

鏌ョ湅 PBS 鏃ュ織锛?

```bash
find labels -name stdout.log | tail
find labels -name stderr.log | tail
find models/jobs -name stdout.log | tail
find models/jobs -name stderr.log | tail
find results/jobs -name stdout.log | tail
find results/jobs -name stderr.log | tail
```

鏌ョ湅褰撳墠 PBS 浣滀笟锛?

```bash
qstat -u $USER
```

---

## 11. 褰撳墠杩欑増涓荤嚎鏈€閲嶈鐨勫彉鍖?

涓庝箣鍓嶇浉姣旓紝褰撳墠鐗堟湰澶氫簡涓変欢闈炲父鍏抽敭鐨勪簨鎯咃細

- notebook 缂?`seaborn` 鏃朵笉鍐嶇洿鎺ュ穿鎺?
- 璁粌闃舵浼氱粺涓€瀵煎嚭閫愭牱鏈娴嬨€乻plit 鍜?history 鍗犱綅鏂囦欢
- 绗竴杞幇鍦ㄥ彲浠ラ€氳繃涓€涓富鎺ц剼鏈畬鎴愶紝鑰屼笉蹇呮墜宸ョ鐞嗘墍鏈夐樁娈?


