# 鏈€灏忕増 ADL 椤圭洰锛欵thene + 1,3-Butadiene

杩欎釜瀛愰」鐩槸褰撳墠浠撳簱閲岀湡姝ｆ帹鑽愪娇鐢ㄧ殑涓诲叆鍙ｏ紝鐩爣涓嶆槸瀹屾暣澶嶇幇鏁寸瘒璁烘枃锛岃€屾槸鎶婃渶灏忕増 active delta-learning 绗竴杞祦绋嬪湪鏈嶅姟鍣ㄤ笂绋冲畾璺戦€氾紝骞朵笖璁╃粨鏋滆兘鐩存帴杩涘叆鍒嗘瀽涓庢眹鎶ャ€?

褰撳墠榛樿璁剧疆锛?

- 浣撶郴锛歚ethene + 1,3-butadiene`
- `baseline`锛歚GFN2-xTB`
- `target`锛欸aussian `wB97X-D/6-31G*`
- 涓绘ā鍨嬶細`ANI`
- 榛樿璁粌璁惧锛歚cuda`
- 榛樿璁粌鐜鍚嶏細`ADL_env`
- 瀛︿範鐩爣锛?
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

## 鐜板湪鎺ㄨ崘鐨勪娇鐢ㄦ柟寮?
涓庝箣鍓嶁€滈€愭潯鏁插崟闃舵鑴氭湰鈥濈殑鏂瑰紡鐩告瘮锛岀幇鍦ㄦ洿鎺ㄨ崘锛?

1. 鍏堣窇 `scripts/run_first_round_pipeline.py`
2. 璺戝畬鍚庣洿鎺ユ墦寮€ `../docs/DATA_ANALYSIS.ipynb`

涔熷氨鏄锛屼富绾垮凡缁忎粠鈥滃彧淇濊瘉绠楀緱瀹屸€濆崌绾т负鈥滅畻瀹屽氨鑳藉垎鏋愨€濄€?

## 鐩綍缁撴瀯

```text
minimal_adl_ethene_butadiene/
鈹溾攢鈹€ configs/
鈹溾攢鈹€ data/
鈹?  鈹溾攢鈹€ raw/
鈹?  鈹斺攢鈹€ processed/
鈹溾攢鈹€ geometries/
鈹?  鈹斺攢鈹€ seed/
鈹溾攢鈹€ labels/
鈹?  鈹溾攢鈹€ gaussian/
鈹?  鈹斺攢鈹€ xtb/
鈹溾攢鈹€ logs/
鈹溾攢鈹€ models/
鈹溾攢鈹€ results/
鈹溾攢鈹€ scripts/
鈹斺攢鈹€ src/minimal_adl/
```

## 鐜鍑嗗
褰撳墠榛樿璁粌鐜鍚嶆槸 `ADL_env`銆傚鏋滀綘鐨?PBS 璁粌鐜涓嶆槸杩欎釜鍚嶅瓧锛屽彲浠ユ敼 `configs/base.yaml` 涓殑 `cluster.conda_env`锛涘鏋滀綘鍙槸鎵撳紑 notebook 鍋氬垎鏋愶紝鍙互缁х画浣跨敤鍗曠嫭鐨?`data_env`銆?

鎺ㄨ崘鐨勬渶灏忎緷璧栨爤鍖呮嫭锛?

- `numpy`
- `PyYAML`
- `matplotlib`
- `seaborn`
- `joblib`
- `scikit-learn`
- `mlatom`
- `torch`
- `torchani`
- `pyh5md`

濡傛灉浣犺琛ラ綈 notebook 缁樺浘鐜锛屽缓璁湪鍒嗘瀽鐜 `data_env` 涓厛琛ユ渶甯哥己鐨勭粯鍥惧簱锛?

```bash
conda activate data_env
python -m pip install "seaborn>=0.12"
```

濡傛灉 `data_env` 閲岃繕缂?`pandas`銆乣matplotlib` 鎴?`scikit-learn`锛屽啀鎸夋姤閿欒ˉ瑁咃紱涓嶅繀涓轰簡鍒嗘瀽 notebook 鎶婃暣濂楄缁冧緷璧栭兘瑁呰繘 `data_env`銆?

## 鍏堝仛鐜鑷
寮€濮嬭窇涓荤嚎涔嬪墠锛屽缓璁厛鍋氫袱姝ワ細

```bash
conda activate ADL_env
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

濡傛灉浣犲凡缁忓湪 GPU 鑺傜偣鍐咃紝涔熷彲浠ョ户缁鏌ワ細

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
```

鑷鎶ュ憡榛樿浼氬啓鍒帮細

- `results/check_environment_latest.json`

## 涓€閿窇瀹屾暣绗竴杞?
鏈€鎺ㄨ崘鐨勫懡浠ゆ槸锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

濡傛灉浣犵涓€娆′笂鏈嶅姟鍣紝鎯冲厛鎻掑叆涓€涓皬鏍锋湰鑱旈€氭祴璇曪細

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs       --with-smoke-tests
```

涓绘帶鑴氭湰鍥哄畾瑕嗙洊锛?

1. 鐜鑷
2. 鍑犱綍姹犵敓鎴?
3. 鍒濆閫夌偣
4. baseline 鏍囨敞
5. target 鏍囨敞
6. delta 鏁版嵁闆嗘瀯寤?
7. 涓绘ā鍨嬭缁?
8. 杈呭姪妯″瀷璁粌
9. 璁粌璇婃柇浜х墿瀵煎嚭
10. UQ 璇勪及
11. 绗?1 杞€夌偣

## 濡備綍鎭㈠鎴栧眬閮ㄩ噸璺?
`run_first_round_pipeline.py` 榛樿 `resume=true`銆備篃灏辨槸璇达紝濡傛灉鏍囧噯浜х墿宸茬粡瀛樺湪锛屽畠浼氳嚜鍔ㄨ烦杩囧凡缁忓畬鎴愮殑闃舵銆?

甯哥敤鍛戒护锛?

鍙粠璁粌闃舵寮€濮嬪線鍚庨噸璺戯細

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --submit-mode-train pbs       --submit-mode-uq pbs
```

寮哄埗閲嶈窇璁粌鍙婂悗缁樁娈碉細

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --force       --submit-mode-train pbs       --submit-mode-uq pbs
```

鍙兂璺戝埌璁粌璇婃柇浜х墿瀵煎嚭涓烘锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --to-stage export_training_diagnostics       --submit-mode-labels pbs       --submit-mode-train pbs
```

## 璁粌鍚庝細鑷姩鐢熸垚鍝簺鏍囧噯鍒嗘瀽鏂囦欢
鍗囩骇鍚庯紝璁粌缁撴潫鍚庝細鑷姩琛ラ綈杩欎簺浜х墿锛?

- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`

UQ 涓庝富鎺ф祦绋嬩骇鐗╁垯浣嶄簬锛?

- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/active_learning_round_history.json`
- `results/pipeline_run_summary.json`

杩欎簺鏂囦欢灏辨槸 `../docs/DATA_ANALYSIS.ipynb` 鐨勯粯璁よ緭鍏ャ€?

## 濡備綍鍒嗘瀽缁撴灉
璁粌鍜?UQ 璺戝畬鍚庯紝鐩存帴鎵撳紑锛?

- [../docs/DATA_ANALYSIS.ipynb](../docs/DATA_ANALYSIS.ipynb)

鏍囧噯璺緞涓嬮€氬父涓嶉渶瑕佸厛鏀?`CONFIG`锛涘鏋滀綘鍒囨崲鍒拌緟鍔╂ā鍨嬪垎鏋愶紝鍙互鎶?`MODEL_VIEW` 鏀规垚 `aux`銆?

notebook 榛樿鍥炵瓟鍥涗釜闂锛屽苟涓斾細鑷姩璇嗗埆鏈€鏂拌疆娆°€佹眹鎬诲巻鍙茶疆娆★細

1. 鏁版嵁闀夸粈涔堟牱
2. 妯″瀷璁粌寰楅『涓嶉『
3. 妯″瀷棰勬祴寰楀噯涓嶅噯
4. 妯″瀷涓轰粈涔堣繖鏍烽娴?

## PBS 浠诲姟鍒嗗伐
褰撳墠閰嶇疆榛樿鍒嗘祦濡備笅锛?

- `xTB` baseline 鏍囨敞锛欳PU 闃熷垪
- Gaussian target 鏍囨敞锛欳PU 闃熷垪
- 涓绘ā鍨嬭缁冿細GPU 闃熷垪
- 杈呭姪妯″瀷璁粌锛欸PU 闃熷垪
- 涓嶇‘瀹氭€ц瘎浼帮細GPU 闃熷垪

褰撳墠 `base.yaml` 閲屽凡缁忕粰鍥涚被浠诲姟閮介鐣欎簡锛?

- `cluster.resources_by_method.baseline.extra_pbs_lines`
- `cluster.resources_by_method.target.extra_pbs_lines`
- `cluster.resources_by_method.training.extra_pbs_lines`
- `cluster.resources_by_method.uncertainty.extra_pbs_lines`

濡傛灉浣犵殑鏈烘埧瑕佹眰棰濆璧勬簮璇彞锛屼緥濡?`#PBS -l gpus=1`锛屽氨鍦ㄥ搴旂殑 `extra_pbs_lines` 閲屽～鍐欍€?

## 杩樻兂鐪嬫洿缁嗙殑璇存槑
寤鸿缁х画璇伙細

- [../docs/WORKFLOW_GUIDE.md](../docs/WORKFLOW_GUIDE.md)
- [../docs/RUNBOOK_ANI_FIRST_ROUND.md](../docs/RUNBOOK_ANI_FIRST_ROUND.md)
- [../docs/RESULT_SUMMARY_ANI_FIRST_ROUND.md](../docs/RESULT_SUMMARY_ANI_FIRST_ROUND.md)


