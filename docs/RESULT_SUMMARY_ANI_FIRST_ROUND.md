# AIQM 闆嗙兢绗竴杞粨鏋滄憳瑕?

杩欎唤鎽樿瀵瑰簲褰撳墠鏈€灏忕増 ADL 绗竴杞富绾垮湪 `ethene + 1,3-butadiene` 浣撶郴涓婄殑鐪熷疄璺戦€氱粨鏋溿€?

## 涓€鍙ヨ瘽缁撹
褰撳墠绗竴杞凡缁忓畬鎴愨€滃嚑浣曟睜鐢熸垚銆佸垵濮嬮€夌偣銆佸弻灞傛爣娉ㄣ€乨elta 鏁版嵁闆嗘瀯寤恒€佷富杈呮ā鍨嬭缁冦€佷笉纭畾鎬ц瘎浼般€佺 1 杞€夌偣鍜屾敹鏁涘垽鏂€濈殑瀹屾暣闂幆锛屽苟涓旀弧瓒冲綋鍓嶉粯璁ゆ敹鏁涙潯浠躲€?

## 鍏抽敭鏁板瓧

- `pool = 400`
- `initial = 250`
- `uncertainty on 400 samples`
- `round 1 selected = 5`
- `uncertain ratio = 3.33%`
- `converged = true`

杩欐剰鍛崇潃锛?

- 涓€寮€濮嬪叡鍑嗗浜?`400` 涓€欓€夊嚑浣?
- 绗?0 杞厛鐢?`250` 涓牱鏈瀯閫犺缁冮泦
- 璁粌鍚庡 `400` 涓牱鏈兘鍋氫簡 UQ 璇勪及
- 鍙湁 `5` 涓牱鏈珮浜庨槇鍊硷紝鍊煎緱浼樺厛琛ユ爣
- 楂樹笉纭畾鎬ф瘮渚?`3.33%` 浣庝簬榛樿 `5%`
- 鍥犳褰撳墠鍙互鍒ゅ畾绗竴杞棴鐜凡缁忚窇閫氬苟杈惧埌褰撳墠鏀舵暃鏉′欢

## 鐜板湪鏂板鐨勬爣鍑嗗垎鏋愪骇鐗?
涓轰簡璁╃粨鏋滆兘鐩存帴杩涘叆 notebook 鍒嗘瀽锛屽綋鍓嶄富绾胯繕浼氱粺涓€杈撳嚭锛?

- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`
- `results/pipeline_run_summary.json`

鍏朵腑锛?

- `train_main_predictions.csv` 璐熻矗閫愭牱鏈宸垎鏋?
- `train_main_history.json` 璐熻矗璁粌鏇茬嚎杈撳叆
- `training_diagnostics.json` 璐熻矗鍛婅瘔 notebook 榛樿搴旇璇诲摢浜涙枃浠?
- `pipeline_run_summary.json` 璐熻矗淇濈暀鏁存潯涓绘帶娴佺▼鐨勯樁娈佃褰?

## 瀵规眹鎶ユ渶鏈夌敤鐨勮〃杈炬柟寮?
濡傛灉浣犺鍦ㄧ粍浼氭垨瀹為獙姹囨姤閲岀敤涓€鍙ヨ瘽姒傛嫭锛屽彲浠ョ洿鎺ヨ锛?

褰撳墠鏈€灏忕増 ADL 绗竴杞凡缁忓畬鎴愪粠鍑犱綍鐢熸垚銆佸垵濮嬮€夌偣銆佸弻灞傛爣娉ㄣ€乨elta 鏁版嵁闆嗘瀯寤恒€佷富杈呮ā鍨嬭缁冦€佷笉纭畾鎬ц瘎浼板埌绗?1 杞€夌偣鍜屾敹鏁涘垽鏂殑瀹屾暣闂幆锛涙湰杞珮涓嶇‘瀹氭€ф瘮渚嬩粎 `3.33%`锛屼綆浜庨粯璁?`5%` 闃堝€硷紝鍥犳鍙垽瀹氬綋鍓嶆祦绋嬪凡缁忚窇閫氬苟婊¤冻绗竴杞敹鏁涙潯浠躲€?

## 涓嬩竴姝ュ缓璁?

- 濡傛灉鍙兂鍋氱粨鏋滄眹鎶ワ紝鐩存帴鎵撳紑 `docs/DATA_ANALYSIS.ipynb`
- 濡傛灉鎯崇户缁 2 杞紝鍙互浼樺厛琛ユ爣杩?`5` 涓牱鏈?
- 濡傛灉涓棿鏌愰樁娈靛け璐ワ紝鐜板湪浼樺厛浣跨敤 `scripts/run_first_round_pipeline.py` 鐨?`resume` 鎴?`--from-stage` 鏈哄埗閲嶈窇


