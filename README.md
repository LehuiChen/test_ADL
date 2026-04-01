# Minimal Active Delta-Learning for Ethene + 1,3-Butadiene

杩欐槸涓€涓潰鍚戞暀瀛︺€佸鐜板拰绗竴杞笂鎵嬬殑鏈€灏忕増 ADL 浠撳簱銆傚畠鍥寸粫 `ethene + 1,3-butadiene` 浣撶郴锛屼繚鐣欎竴鏉″敖閲忕煭浣嗚兘鐪熸闂幆鐨勪富鍔?delta-learning 涓荤嚎锛?

- `baseline`: `GFN2-xTB`
- `target`: Gaussian `wB97X-D/6-31G*`
- 涓绘ā鍨? `ANI`
- 瀛︿範鐩爣:
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

杩欎唤浠撳簱鐜板湪鐨勭洰鏍囦笉鍙槸鈥滅涓€杞兘璺戦€氣€濓紝鑰屾槸鈥滆窇瀹屽氨鑳界洿鎺ュ垎鏋愬拰姹囨姤鈥濄€?

## Recommended Docs

1. [docs/README.md](./docs/README.md)
2. [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md)
3. [docs/WORKFLOW_GUIDE.md](./docs/WORKFLOW_GUIDE.md)
4. [docs/RUNBOOK_ANI_FIRST_ROUND.md](./docs/RUNBOOK_ANI_FIRST_ROUND.md)
5. [docs/DATA_ANALYSIS.ipynb](./docs/DATA_ANALYSIS.ipynb)
6. [docs/RESULT_SUMMARY_ANI_FIRST_ROUND.md](./docs/RESULT_SUMMARY_ANI_FIRST_ROUND.md)

## 杩欐鍗囩骇鍚庣殑涓荤嚎鑳藉姏
褰撳墠鎺ㄨ崘涓荤嚎浣嶄簬 [minimal_adl_ethene_butadiene](./minimal_adl_ethene_butadiene/)锛屽凡缁忓崌绾т负鈥滃彲澶嶈窇銆佸彲鍒嗘瀽銆佸彲姹囨姤鈥濈殑绗竴杞祦绋嬶細

- 鏂板涓€閿富鎺ц剼鏈?`scripts/run_first_round_pipeline.py`
- 淇濈暀鐜版湁鍗曢樁娈佃剼鏈紝渚夸簬灞€閮ㄩ噸璺戝拰鎺掗敊
- 璁粌鍚庤嚜鍔ㄨˉ榻?notebook 榛樿闇€瑕佺殑鍒嗘瀽浜х墿
- `docs/DATA_ANALYSIS.ipynb` 榛樿鐩存帴璇诲彇鏍囧噯杈撳嚭璺緞
- 缂哄け鍙€夋枃浠舵椂 notebook 浼氭竻鏅伴檷绾э紝鑰屼笉鏄暣鏈姤閿?

## 涓€閿窇绗竴杞?
鍦ㄦ湇鍔″櫒浠撳簱鏍圭洰褰曟洿鏂颁唬鐮佸悗锛岃繘鍏ュ瓙椤圭洰鐩綍鎵ц锛?

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

濡傛灉浣犳兂鍏堟彃鍏ヤ竴涓皬瑙勬ā鑱旈€氭鏌ワ紝鍐嶈窇瀹屾暣涓荤嚎锛?

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs       --with-smoke-tests
```

杩欎釜涓绘帶鑴氭湰鍥哄畾缂栨帓浠ヤ笅闃舵锛?

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

瀹冮粯璁ゅ惎鐢?`resume`锛屽鏋滄煇闃舵宸叉湁鎴愬姛浜х墿锛屼細鑷姩璺宠繃锛涗篃鏀寔 `--from-stage`銆乣--to-stage` 鍜?`--force` 鍋氬眬閮ㄩ噸璺戙€?

## 璺戝畬涔嬪悗浼氬鍑哄摢浜涙爣鍑嗗垎鏋愪骇鐗?
鍗囩骇鍚庯紝绗竴杞缁冨拰 UQ 瀹屾垚鍚庝細缁熶竴杈撳嚭杩欎簺鏍囧噯鏂囦欢锛?

`models/`

- `training_summary.json`
- `training_state.json`
- `training_split.json`
- `train_main_predictions.csv`
- `train_aux_predictions.csv`
- `train_main_history.json`
- `train_aux_history.json`
- `training_diagnostics.json`

`results/`

- `uncertainty_latest.json`
- `round_001_selection_summary.json`
- `round_001_selected_manifest.json`
- `active_learning_round_history.json`
- `pipeline_run_summary.json`
- `check_environment_latest.json`

鍏朵腑锛?

- `predictions.csv` 璐熻矗閫愭牱鏈宸垎鏋?
- `history.json` 璐熻矗璁粌鏇茬嚎
- `training_diagnostics.json` 璐熻矗鍛婅瘔 notebook 搴旇榛樿璇诲摢浜涙枃浠?
- `pipeline_run_summary.json` 璐熻矗璁板綍涓绘帶娴佺▼鐨勯樁娈电姸鎬?

## 濡備綍鍒嗘瀽缁撴灉
鍗囩骇鍚庣殑 notebook 浣嶄簬 [docs/DATA_ANALYSIS.ipynb](./docs/DATA_ANALYSIS.ipynb)銆?

瀹冮粯璁ゅ洿缁曞洓涓棶棰樼粍缁囷細

1. 鏁版嵁闀夸粈涔堟牱
2. 妯″瀷璁粌寰楅『涓嶉『
3. 妯″瀷棰勬祴寰楀噯涓嶅噯
4. 妯″瀷涓轰粈涔堣繖鏍烽娴?

鏍囧噯璺緞涓嬶紝浼樺厛鐩存帴璇诲彇锛?

- `models/train_main_history.json`
- `models/train_main_predictions.csv`
- `models/training_summary.json`
- `results/uncertainty_latest.json`
- `results/active_learning_round_history.json` 鎴?`results/round_*_selection_summary.json`

濡傛灉浣犵殑鏈嶅姟鍣ㄤ骇鐗╄矾寰勫拰鏍囧噯璺緞涓€鑷达紝閫氬父涓嶉渶瑕佸厛鎵嬫敼 notebook 椤堕儴 `CONFIG`銆?

## 鐜璇存槑
褰撳墠 `base.yaml` 閲岀殑 PBS 榛樿鐜鍚嶄粛鐒舵槸 `ADL_env`锛岀敤浜庤缁冦€佹爣娉ㄥ拰 UQ 涓绘祦绋嬨€? 
濡傛灉浣犲彧鏄湪鏈嶅姟鍣ㄤ笂鎵撳紑鍒嗘瀽 notebook锛屽彲浠ョ户缁娇鐢ㄥ崟鐙殑 `data_env`銆備篃灏辨槸璇达細

- 璁粌銆佹爣娉ㄣ€乁Q锛氶粯璁ゆ寜 `conda activate ADL_env`
- notebook 鍒嗘瀽涓庡彲瑙嗗寲锛氬彲浠ヤ娇鐢?`conda activate data_env`

渚濊禆鏂归潰锛宍minimal_adl_ethene_butadiene/requirements.txt` 宸茶ˉ鍏?`seaborn`锛岃繖鏍?notebook 鍦ㄥ父瑙勭幆澧冧笅鍙互鐩存帴缁樺浘锛涘鏋滄湇鍔″櫒鐜閲屾殏鏃舵病鏈?`seaborn`锛宯otebook 涔熶細鑷姩闄嶇骇鍒?`matplotlib` 椋庢牸缁х画杩愯銆?

## 浠撳簱閲岃繕鏈変粈涔?
鍘嗗彶鍙傝€冪洰褰曚粛鐒朵繚鐣欙紝浣嗗綋鍓嶄笉浣滀负鏂版墜涓诲叆鍙ｏ細

- `adl/`
- `static/`

瀹冧滑鏇撮€傚悎瀵圭収璁烘枃鎬濊矾锛屼笉寤鸿绗竴娆″鐜版椂鐩存帴浠庨噷闈㈢户缁紑鍙戙€?

## 闆嗙兢鍚屾寤鸿
鎺ㄨ崘鍦ㄦ湇鍔″櫒涓婁繚鐣欏畬鏁翠粨搴?clone锛岃€屼笉鏄彧鎷疯礉瀛愮洰褰曘€傛爣鍑嗘洿鏂版祦绋嬫槸锛?

```bash
cd /share/home/Chenlehui/work
git clone https://github.com/LehuiChen/test_ADL.git
cd test_ADL
git status
```

浠ュ悗鏈湴鎺ㄩ€佹柊鐗堟湰鍚庯紝鏈嶅姟鍣ㄧ粺涓€杩欐牱鏇存柊锛?

```bash
cd /share/home/Chenlehui/work/test_ADL
git pull --ff-only
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
```

## 璁烘枃鏉ユ簮

- Yaohuang Huang, Yi-Fan Hou, Pavlo O. Dral. *Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations*. Mach. Learn.: Sci. Technol. 2025.
- ChemRxiv 棰勫嵃鏈? [10.26434/chemrxiv-2024-fb02r](https://doi.org/10.26434/chemrxiv-2024-fb02r)
- MLatom 瀹樻柟浠撳簱: [dralgroup/mlatom](https://github.com/dralgroup/mlatom)

## 涓夋鏋跺苟鍒楀伐绋嬶紙ANI / MACE / NequIP锛?
褰撳墠浠撳簱淇濈暀浜嗕笁涓苟鍒楃洰褰曪紝浜掍笉瑕嗙洊锛?
- ANI锛堝師濮嬩富绾匡級锛歚minimal_adl_ethene_butadiene`
- MACE锛堝彲杩愯锛夛細`minimal_adl_ethene_butadiene_mace`
- NequIP锛堥鐣欐帴鍙ｇ増锛夛細`minimal_adl_ethene_butadiene_nequip`

璇存槑锛?
- 涓変釜宸ョ▼鍚勮嚜鎷ユ湁鐙珛鐨?`data/`銆乣models/`銆乣results/`銆乣labels/`銆?- MACE 鐗堟湰澶嶇敤鐜版湁 ADL 绠＄嚎锛屽彲鐩存帴璺戝畬鏁寸涓€杞€?- NequIP 鐗堟湰褰撳墠鐢ㄤ簬宸ョ▼棰勭暀锛氶厤缃彲璇嗗埆锛岃缁冮樁娈典細鏄庣‘鎶?`NotImplementedError`锛屼究浜庡悗缁户缁疄鐜般€?
杩愯鏂囨。锛?
- [docs/MACE_RUNBOOK.md](./docs/MACE_RUNBOOK.md)
- [docs/NEQUIP_RUNBOOK.md](./docs/NEQUIP_RUNBOOK.md)




