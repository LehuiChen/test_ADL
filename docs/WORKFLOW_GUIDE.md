# 娴佺▼浠嬬粛

杩欎唤鏂囨。闈㈠悜绗竴娆℃帴瑙﹁繖涓粨搴撶殑鍚屽锛岄粯璁や綘涓嶆槸璁＄畻鍖栧鑳屾櫙锛屼篃涓嶆槸鏈哄櫒瀛︿範鑳屾櫙銆傜洰鏍囦笉鏄妸鎵€鏈夋湳璇竴娆¤瀹岋紝鑰屾槸璁╀綘鍏堝缓绔嬩竴寮犳竻鏅扮殑鈥滃叏灞€鍦板浘鈥濓細

- 杩欎釜椤圭洰鍦ㄥ仛浠€涔?
- 姣忎竴姝ヤ负浠€涔堝瓨鍦?
- 鍏抽敭鏂囦欢鍒嗗埆璐熻矗浠€涔?
- 鍏紡鍒板簳鍦ㄨ浠€涔?
- 璺戝畬浠ュ悗搴旇鐪嬪摢浜涚粨鏋?

鏈枃鍙鐩栧綋鍓嶆帹鑽愪富绾?`minimal_adl_ethene_butadiene/`锛屼笉灞曞紑浠撳簱涓殑鍘嗗彶鐩綍 `adl/` 鍜?`static/`銆?

## 1. 椤圭洰鍦ㄥ仛浠€涔?
濡傛灉鍙敤涓€鍙ユ棩甯歌瑷€瑙ｉ噴锛岃繖涓」鐩鍋氱殑鏄細

鎴戜滑鎯冲緱鍒颁竴涓€滅畻寰楀揩锛屼絾灏介噺鎺ヨ繎楂樼簿搴﹂噺鍖栫粨鏋溾€濈殑鏈哄櫒瀛︿範鍔胯兘妯″瀷銆?

杩欓噷浼氬弽澶嶅嚭鐜板洓涓叧閿瘝锛?

- `baseline`
  鎸囦究瀹溿€佸揩閫熴€佽兘澶ц妯¤窇鐨勫弬鑰冩柟娉曘€傝繖閲屾槸 `GFN2-xTB`銆傚畠鐨勪紭鐐规槸蹇紝缂虹偣鏄簿搴︿笉濡傛洿楂樼骇鐨勯噺鍖栨柟娉曘€?
- `target`
  鎸囨垜浠湡姝ｅ笇鏈涙帴杩戠殑楂樼簿搴︽爣绛俱€傝繖閲屾槸 Gaussian 鐨?`wB97X-D/6-31G*`銆傚畠鏇村噯锛屼絾涔熸洿鎱€佹洿璐点€?
- `delta-learning`
  涓嶈妯″瀷鐩存帴鍘诲楂樼簿搴︾粷瀵瑰€硷紝鑰屾槸鍙鈥滈珮绮惧害缁撴灉姣斾綆绮惧害缁撴灉澶氬嚭鏉ュ灏戜慨姝ｉ噺鈥濄€?
- `active learning`
  涓嶆槸鎶婂嚑浣曟睜閲屾墍鏈夋牱鏈兘鍋氶珮鎴愭湰鏍囨敞锛岃€屾槸鍏堣缁冧竴涓垵鐗堟ā鍨嬶紝鍐嶇敤涓嶇‘瀹氭€у幓鎸戔€滄渶鍊煎緱琛ユ爣鈥濈殑鏍锋湰銆?

鎶婂畠浠繛鎴愪竴鍙ユ洿瀹屾暣鐨勮瘽锛屽氨鏄細

鍏堣 `xTB` 缁欐墍鏈夊嚑浣曟彁渚?baseline锛屽啀鐢ㄨ緝灏戠殑 Gaussian 鏍囩鏋勯€?`delta` 鏁版嵁闆嗭紝璁粌涓绘ā鍨嬪拰杈呭姪妯″瀷锛岀敤涓よ€呴娴嬪樊寮備及璁′笉纭畾鎬э紝鐒跺悗鍙妸鏈€涓嶇‘瀹氱殑鏍锋湰閫佽繘涓嬩竴杞爣娉ㄣ€?

## 2. 鎬绘祦绋嬪浘

```mermaid
flowchart TD
    A["鐜鍑嗗"] --> B["鍑犱綍姹?]
    B --> C["鍒濆閫夌偣"]
    C --> D["smoke test"]
    D --> E["鏍囨敞"]
    E --> F["delta 鏁版嵁闆?]
    F --> G["涓绘ā鍨嬭缁?]
    G --> H["杈呭姪妯″瀷璁粌"]
    H --> I["涓嶇‘瀹氭€ц瘎浼?]
    I --> J["绗?1 杞€夌偣"]
    J --> K["鏀舵暃鍒ゆ柇"]

    A1["妫€鏌?Python / MLatom / xTB / Gaussian / GPU"] -.-> A
    B1["浠庣瀛愮粨鏋勯殢鏈哄井鎵扮敓鎴愬嚑浣曟睜"] -.-> B
    C1["绗?0 杞厛閫夊嚭鍒濆璁粌鏍锋湰"] -.-> C
    D1["鍏堝仛灏戦噺鑱旈€氭鏌ワ紝閬垮厤鏁存壒澶辫触"] -.-> D
    E1["寰楀埌 baseline 涓?target 鏍囩"] -.-> E
    F1["鏋勯€?delta_E 涓?delta_F"] -.-> F
    G1["涓绘ā鍨嬪涔?delta_E + delta_F"] -.-> G
    H1["杈呭姪妯″瀷鍙涔?delta_E"] -.-> H
    I1["鐢ㄤ富杈呮ā鍨嬪樊鍊煎仛 UQ"] -.-> I
    J1["鎸変笉纭畾鎬ч€夊嚭 round 1 鏂版牱鏈?] -.-> J
    K1["楂樹笉纭畾鎬ф瘮渚嬩綆浜庨槇鍊煎垯鍒や负鏀舵暃"] -.-> K
```

鍦ㄥ綋鍓嶅崌绾у悗鐨勪富绾块噷锛岃繖涓祦绋嬪彲浠ョ洿鎺ョ敱锛?

- `minimal_adl_ethene_butadiene/scripts/run_first_round_pipeline.py`

涓€閿紪鎺掑畬鎴愩€?

## 3. 姣忎竴姝ョ殑杈撳叆銆佽緭鍑恒€佺洰鐨?

| 闃舵 | 杈撳叆 | 鍋氫簡浠€涔?| 杈撳嚭 | 鐩殑 |
| --- | --- | --- | --- | --- |
| 鐜鍑嗗 | `configs/base.yaml`銆佹湇鍔″櫒鐜銆乣ADL_env` | 妫€鏌?Python 鍖呫€亁TB銆丟aussian銆丟PU 鍜?MLatom 鑱旈€氭儏鍐?| `results/check_environment_latest.json` | 鍏堢‘璁ゅ悗闈笉浼氬洜鐜闂鏁存壒澶辫触 |
| 鍑犱綍姹?| `geometries/seed/da_eqmol_seed.xyz` | 瀵圭瀛愮粨鏋勫仛闅忔満寰壈锛岀敓鎴愬€欓€夊嚑浣曟睜 | `data/raw/geometries/`銆乣data/raw/geometry_pool_manifest.json` | 鍑嗗涓诲姩瀛︿範鐨勫€欓€夋睜 |
| 鍒濆閫夌偣 | 鍑犱綍姹?manifest | 绗?0 杞厛浠庢睜涓寫鍑哄垵濮嬭缁冩牱鏈?| `data/raw/initial_selection_manifest.json` | 缁欑涓€杞缁冨噯澶囪捣濮嬫暟鎹?|
| smoke test | 灏戦噺宸查€夋牱鏈拰褰撳墠鐜 | 鍏堝仛灏戦噺 `xTB` / Gaussian 鑱旈€氭鏌?| 灏戦噺 `label.json`銆乣status.json` 鍜屾棩蹇?| 閬垮厤鐩存帴鎻愪氦瀹屾暣鎵规鎵嶅彂鐜拌矾寰勬垨 PBS 鏈夐棶棰?|
| 鏍囨敞 | 鍒濆鏍锋湰 manifest銆乥aseline/target 閰嶇疆 | 鍒嗗埆璁＄畻 `GFN2-xTB` 涓?`wB97X-D/6-31G*` 鐨勮兘閲忓拰鍔?| `labels/xtb/<sample_id>/label.json`銆乣labels/gaussian/<sample_id>/label.json` | 寰楀埌鏋勯€?delta 鏁版嵁闆嗘墍闇€鐨勪袱濂楁爣绛?|
| delta 鏁版嵁闆?| 鍑犱綍鏂囦欢銆乥aseline 鏍囩銆乼arget 鏍囩 | 瀵归綈鏍锋湰骞惰绠楄兘閲忓樊鍜屽姏宸?| `data/processed/delta_dataset.npz`銆乣data/processed/delta_dataset_metadata.json` | 缁欒缁冮樁娈垫彁渚涚粺涓€杈撳叆 |
| 涓绘ā鍨嬭缁?| delta 鏁版嵁闆?| 瀛︿範 `delta_E + delta_F` | `models/delta_main_model.pt` 鍙婅缁冩憳瑕?| 寤虹珛涓婚娴嬫ā鍨?|
| 杈呭姪妯″瀷璁粌 | delta 鏁版嵁闆?| 鍙涔?`delta_E` | `models/delta_aux_model.pt` 鍙婅缁冩憳瑕?| 褰㈡垚绗簩涓瑙掞紝鐢ㄤ簬 UQ |
| 璁粌璇婃柇瀵煎嚭 | 璁粌鐘舵€佷笌妯″瀷鏂囦欢 | 缁熶竴瀵煎嚭 split銆侀€愭牱鏈娴嬨€乭istory 涓庤瘖鏂憳瑕?| `models/training_split.json`銆乣models/train_main_predictions.csv`銆乣models/train_main_history.json` 绛?| 璁?notebook 涓嶅啀缂哄垎鏋愯緭鍏?|
| 涓嶇‘瀹氭€ц瘎浼?| 涓?杈呮ā鍨嬨€佸畬鏁村嚑浣曟睜 | 瀵规睜涓牱鏈仛棰勬祴骞惰绠?UQ | `results/uncertainty_latest.json` | 鎵惧嚭妯″瀷鏈€娌℃妸鎻＄殑鏍锋湰 |
| 绗?1 杞€夌偣 | UQ 缁撴灉銆佸凡鏍囨敞鏍锋湰鍒楄〃 | 杩囨护宸叉爣娉ㄦ牱鏈苟鎸?UQ 浠庨珮鍒颁綆閫夌偣 | `results/round_001_selection_summary.json`銆乣results/round_001_selected_manifest.json` | 涓轰笅涓€杞ˉ鏍囧仛鍑嗗 |
| 鏀舵暃鍒ゆ柇 | 绗?1 杞€夌偣缁熻 | 璁＄畻楂樹笉纭畾鎬ф牱鏈瘮渚?| `converged = true/false` | 鍐冲畾鏄惁缁х画涓嬩竴杞富鍔ㄥ涔?|

## 4. 鏍稿績鏂囦欢璇存槑琛?
涓嬮潰鍙鐩?`minimal_adl_ethene_butadiene/` 鐨勬牳蹇冩枃浠讹紝鎸夋ā鍧楀垎缁勮鏄庛€?

### 4.1 閰嶇疆涓庤緭鍏?

| 鏂囦欢 | 鐢ㄩ€?|
| --- | --- |
| `minimal_adl_ethene_butadiene/configs/base.yaml` | 鏁翠釜椤圭洰鐨勬€婚厤缃叆鍙ｏ紝瀹氫箟璺緞銆侀噰鏍锋暟銆佽缁冨弬鏁般€佷富鍔ㄥ涔犻槇鍊笺€丳BS 璧勬簮鍜岀幆澧冨潡銆傚綋鍓嶉粯璁?PBS 璁粌鐜鍚嶆槸 `ADL_env`銆?|
| `minimal_adl_ethene_butadiene/geometries/seed/da_eqmol_seed.xyz` | 绉嶅瓙鍑犱綍锛屽嚑浣曟睜灏辨槸鍦ㄥ畠鐨勫熀纭€涓婂仛闅忔満寰壈寰楀埌鐨勩€?|

### 4.2 娴佺▼鑴氭湰

| 鏂囦欢 | 鐢ㄩ€?|
| --- | --- |
| `minimal_adl_ethene_butadiene/scripts/sample_initial_geometries.py` | 浠庣瀛愮粨鏋勭敓鎴愬嚑浣曟睜锛屽苟鍐欏嚭 pool manifest銆?|
| `minimal_adl_ethene_butadiene/scripts/active_learning_loop.py` | 璐熻矗鍒濆閫夌偣锛屼互鍙婃牴鎹?UQ 缁撴灉閫夋嫨涓嬩竴杞牱鏈€?|
| `minimal_adl_ethene_butadiene/scripts/run_xtb_labels.py` | 鎵归噺鎻愪氦 baseline `xTB` 鏍囨敞浠诲姟銆?|
| `minimal_adl_ethene_butadiene/scripts/run_target_labels.py` | 鎵归噺鎻愪氦 target Gaussian 鏍囨敞浠诲姟銆?|
| `minimal_adl_ethene_butadiene/scripts/build_delta_dataset.py` | 姹囨€?baseline 鍜?target 缁撴灉锛屾瀯寤?`delta_dataset.npz`銆?|
| `minimal_adl_ethene_butadiene/scripts/train_main_model.py` | 璁粌涓绘ā鍨嬶紝瀛︿範 `delta_E + delta_F`銆?|
| `minimal_adl_ethene_butadiene/scripts/train_aux_model.py` | 璁粌杈呭姪妯″瀷锛屽彧瀛︿範 `delta_E`銆?|
| `minimal_adl_ethene_butadiene/scripts/evaluate_uncertainty.py` | 鐢ㄤ富妯″瀷鍜岃緟鍔╂ā鍨嬪鍑犱綍姹犲仛棰勬祴锛岃緭鍑?UQ 缁撴灉銆?|
| `minimal_adl_ethene_butadiene/scripts/check_environment.py` | 妫€鏌ヤ緷璧栥€佸懡浠ゃ€丟PU銆丮Latom-xTB 鑱旈€氭儏鍐碉紝鏄紑璺戝墠鏈€閲嶈鐨勮嚜妫€鑴氭湰銆?|

### 4.3 鏂板鐨勪富鎺т笌鍒嗘瀽鑴氭湰

| 鏂囦欢 | 鐢ㄩ€?|
| --- | --- |
| `minimal_adl_ethene_butadiene/scripts/run_first_round_pipeline.py` | 涓€閿紪鎺掔涓€杞富绾匡紝鏀寔 `resume`銆乣--from-stage`銆乣--to-stage` 鍜?`--force`銆?|
| `minimal_adl_ethene_butadiene/scripts/export_training_diagnostics.py` | 鎶?split銆乸redictions銆乭istory 鍜岃缁冭瘖鏂俊鎭暣鐞嗘垚 notebook 榛樿鍙鐨勬爣鍑嗘枃浠躲€?|

### 4.4 鏍稿績妯″潡

| 鏂囦欢 | 鐢ㄩ€?|
| --- | --- |
| `minimal_adl_ethene_butadiene/src/minimal_adl/geometry.py` | 璇诲啓鍑犱綍鏂囦欢銆佺敓鎴愰殢鏈哄井鎵板嚑浣曘€佺淮鎶?manifest銆?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/dataset.py` | 璇诲彇鏍囨敞缁撴灉锛屾瀯寤哄拰鍔犺浇 `delta` 鏁版嵁闆嗐€?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/label_jobs.py` | 缁勭粐鎵归噺鏍囨敞浠诲姟锛屾敮鎸佹湰鍦拌繍琛屻€丳BS 鍗曟牱鏈彁浜ゅ拰 worker 妯″紡銆?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/mlatom_bridge.py` | 鎶婇」鐩€昏緫鎺ュ埌 MLatom锛岃礋璐ｆ柟娉曞垱寤恒€佹爣娉ㄣ€佹暟鎹泦杞垚 MLatom 鏁版嵁搴撱€?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/training.py` | 鍒涘缓涓?杈呮ā鍨?bundle锛岃缁冩ā鍨嬶紝璇诲彇璁粌鐘舵€併€?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/delta_model.py` | 瀹氫箟涓绘ā鍨嬪拰杈呭姪妯″瀷鐨勬渶灏忓皝瑁咃紝璐熻矗璁粌銆侀娴嬨€佹寚鏍囨眹鎬诲拰鍒嗘瀽浜х墿瀵煎嚭銆?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/uncertainty.py` | 璁＄畻姣忎釜鏍锋湰鐨?UQ锛屽苟鏍规嵁闃堝€肩敓鎴愪笅涓€杞€夌偣缁撴灉銆?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/pbs.py` | 鐢熸垚 PBS 鑴氭湰銆佹彁浜や綔涓氥€佺瓑寰呯姸鎬佹枃浠躲€?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/config.py` | 鍔犺浇 YAML 閰嶇疆锛屽苟鎶婄浉瀵硅矾寰勮В鏋愭垚缁濆璺緞銆?|
| `minimal_adl_ethene_butadiene/src/minimal_adl/io_utils.py` | JSON銆丆SV 鍜屾枃鏈鍐欍€佺洰褰曞垱寤恒€佹椂闂存埑绛夐€氱敤宸ュ叿銆?|

### 4.5 杈呭姪鑴氭湰

| 鏂囦欢 | 鐢ㄩ€?|
| --- | --- |
| `minimal_adl_ethene_butadiene/scripts/execute_label_job.py` | 鐪熸鎵ц鍗曚釜鏍锋湰鐨?baseline 鎴?target 鏍囨敞浠诲姟銆?|
| `minimal_adl_ethene_butadiene/scripts/execute_label_batch.py` | 鍦ㄤ竴涓?PBS worker 浣滀笟閲屽苟琛屾墽琛屼竴鎵规爣娉ㄤ换鍔°€?|
| `minimal_adl_ethene_butadiene/scripts/optimize_ts.py` | 鍙€夊伐鍏凤紝鐢?MLatom 閰嶅悎 `xTB` 鎴?Gaussian 鍋?TS 浼樺寲锛屼笉灞炰簬绗竴杞富绾裤€?|

## 5. 鏍稿績鍘熺悊涓庡叕寮?

### 5.1 鍑犱綍閲囨牱
鍑犱綍姹犱笉鏄嚟绌烘潵鐨勶紝鑰屾槸鍦ㄧ瀛愮粨鏋勯檮杩戝仛灏忓箙闅忔満鎵板姩锛?

\[
R_{new} = R_{seed} + \operatorname{clip}(\epsilon, -d_{max}, d_{max})
\]

鐩磋鐞嗚В鏄細鍥寸潃涓€涓凡鐭ュ悎鐞嗙粨鏋勶紝杞诲井鎺ㄤ竴鎺ㄣ€佹媺涓€鎷夛紝寰楀埌涓€鎵圭浉浼间絾涓嶅畬鍏ㄧ浉鍚岀殑鍑犱綍銆?

- `R_seed` 鏄瀛愬嚑浣曞潗鏍?
- `\epsilon` 鏄殢鏈烘壈鍔?
- `clip` 鎶婅繃澶х殑浣嶇Щ鎴柇鍒板厑璁歌寖鍥村唴
- `d_max` 鏄渶澶у厑璁镐綅绉?

杩欎竴闃舵鐨勬剰涔夋槸锛氭棦淇濈暀澶氭牱鎬э紝鍙堥伩鍏嶆牱鏈竴涓婃潵灏卞亸鍒扮壒鍒笉鍚堢悊鐨勭粨鏋勩€?

### 5.2 delta 瀛︿範
椤圭洰涓嶈妯″瀷鐩存帴瀛﹂珮绮惧害缁濆鍊硷紝鑰屾槸鍙淇閲忥細

\[
\Delta E = E_{target} - E_{baseline}
\]

\[
\Delta F = F_{target} - F_{baseline}
\]

閫氫織鍦拌锛?

- `baseline` 宸茬粡缁欏嚭涓€涓€滃樊涓嶅鐨勭瓟妗堚€?
- 妯″瀷鍙渶瑕佸鈥滆繕宸灏戜慨姝ｉ噺鈥?
- 杩欐牱閫氬父姣旂洿鎺ュ `target` 鏇寸渷鏁版嵁锛屼篃鏇村鏄撴敹鏁?

### 5.3 涓绘ā鍨嬪拰杈呭姪妯″瀷鍒嗗埆瀛︿粈涔?
涓绘ā鍨嬪涔狅細

\[
\text{main model}: (\Delta E, \Delta F)
\]

涔熷氨鏄悓鏃跺涔犺兘閲忓樊鍜屽姏宸€?

杈呭姪妯″瀷瀛︿範锛?

\[
\text{aux model}: \Delta E
\]

瀹冨彧瀛︿範鑳介噺宸紝涓昏浣滅敤涓嶆槸鏇夸唬涓绘ā鍨嬶紝鑰屾槸鍜屼富妯″瀷褰㈡垚涓や釜涓嶅悓瑙嗚锛岀敤鏉ヤ及璁′笉纭畾鎬с€?

### 5.4 涓嶇‘瀹氭€?
褰撳墠鏈€灏忕増娴佺▼閲囩敤闈炲父鐩磋鐨勫畾涔夛細

\[
UQ = \left| pred\_main\_{\Delta E} - pred\_aux\_{\Delta E} \right|
\]

濡傛灉涓や釜妯″瀷瀵瑰悓涓€鏍锋湰鐨?`delta_E` 棰勬祴宸緱寰堝ぇ锛岄€氬父璇存槑杩欎釜鏍锋湰澶勫湪妯″瀷杩樹笉鐔熸倝鐨勫尯鍩燂紝鍥犳鍊煎緱浼樺厛琛ユ爣銆?

### 5.5 鏀舵暃鍒ゆ嵁
绗?1 杞悗锛屼細缁熻楂樹笉纭畾鎬ф牱鏈瘮渚嬶細

\[
uncertain\_ratio = \frac{num\_uncertain\_samples}{num\_pool\_samples}
\]

濡傛灉杩欎釜姣斾緥宸茬粡寰堜綆锛岃鏄庡嚑浣曟睜涓ぇ澶氭暟鏍锋湰妯″瀷閮藉凡缁忔瘮杈冩湁鎶婃彙銆傚綋鍓嶉粯璁ゆ敹鏁涢槇鍊兼槸 `5%`銆?

### 5.6 RMSE 鍜?PCC 鐨勬剰涔?
甯歌鎸囨爣鏈?`RMSE` 鍜?`PCC`銆?

鍧囨柟鏍硅宸細

\[
RMSE = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(y_i - \hat{y}_i)^2}
\]

瀹冭　閲忛娴嬪€间笌鐪熷疄鍊煎钩鍧囧樊澶氬皯锛岃秺灏忚秺濂姐€?

鐨皵閫婄浉鍏崇郴鏁帮細

\[
PCC = \frac{\operatorname{cov}(y, \hat{y})}{\sigma_y \sigma_{\hat{y}}}
\]

瀹冭　閲忛娴嬭秼鍔夸笌鐪熷疄瓒嬪娍鏄惁涓€鑷达紝瓒婃帴杩?`1` 瓒婂ソ銆?

## 6. 濡備綍鍒ゆ柇璁粌缁撴灉濂藉潖
鍙互鍏堟姄浣忚繖浜涙渶閲嶈鐨勫師鍒欙細

- `energy RMSE` 瓒婂皬瓒婂ソ
- `gradient RMSE` 瓒婂皬瓒婂ソ
- `PCC` 瓒婃帴杩?`1` 瓒婂ソ
- 楠岃瘉闆嗘瘮璁粌闆嗘洿閲嶈
- 璁粌鎴愬姛涓嶇瓑浜庝富鍔ㄥ涔犳敹鏁?

涔熷氨鏄锛岃嚦灏戣鍒嗘垚涓ゅ眰鐪嬶細

- 绗竴灞傦細妯″瀷鏈夋病鏈夊鍒颁笢瑗?
- 绗簩灞傦細妯″瀷瀛﹀埌鐨勪笢瑗垮涓嶅鏀寔杩欎竴杞富鍔ㄥ涔犵粨鏉?

## 7. 濡備綍鍒ゆ柇杩欐绗竴杞负浠€涔堢畻鈥滆窇閫氣€?
褰撳墠杩欐鐪熷疄缁撴灉鎽樿鏄細

- `pool = 400`
- `initial = 250`
- `uncertainty on 400 samples`
- `round 1 selected = 5`
- `uncertain ratio = 3.33%`
- `converged = true`

鎶婅繖浜涙暟瀛楃炕璇戞垚鏇村鏄撶悊瑙ｇ殑璇濓紝灏辨槸锛?

- 涓€寮€濮嬪叡鍑嗗浜?400 涓€欓€夊嚑浣?
- 绗?0 杞厛鐢?250 涓牱鏈瀯閫犱簡绗竴鐗堣缁冩暟鎹?
- 璁粌瀹屾垚鍚庯紝瀵?400 涓睜涓牱鏈兘鍋氫簡 UQ 璇勪及
- 鏈€缁堝彧鏈?5 涓牱鏈珮浜庨槇鍊硷紝鍊煎緱浼樺厛杩涘叆涓嬩竴杞?
- 楂樹笉纭畾鎬ф瘮渚嬫槸 `3.33%`锛屼綆浜庨粯璁ょ殑 `5%`
- 鍥犳褰撳墠绗竴杞凡缁忔弧瓒虫渶灏忛棴鐜窇閫氬苟杈惧埌褰撳墠鏀舵暃鏉′欢

## 8. 鐜板湪鎺ㄨ崘鎬庝箞鎵ц
鍗囩骇鍚庣殑鎺ㄨ崘鍛戒护鏄細

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
conda activate ADL_env
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

璺戝畬浠ュ悗鐩存帴鎵撳紑锛?

- `docs/DATA_ANALYSIS.ipynb`

鏍囧噯璺緞涓嬩紭鍏堣鍙栵細

- `models/train_main_predictions.csv`
- `models/train_main_history.json`
- `models/training_diagnostics.json`
- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/pipeline_run_summary.json`

## 9. 寤鸿鎬庝箞缁х画璇?
濡傛灉浣犳槸绗竴娆℃帴瑙﹁繖涓」鐩紝鎺ㄨ崘椤哄簭鏄細

1. 鍏堣 `minimal_adl_ethene_butadiene/README.md`
2. 鍐嶈杩欎唤 `娴佺▼浠嬬粛.md`
3. 鏈€鍚庢墦寮€ `docs/DATA_ANALYSIS.ipynb`


