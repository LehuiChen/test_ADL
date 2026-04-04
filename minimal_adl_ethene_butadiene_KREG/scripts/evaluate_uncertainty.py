from __future__ import annotations

raise SystemExit(
    "evaluate_uncertainty.py 已退役。"
    " 这个 KREG 工程现在通过 MD 轨迹帧做不确定性驱动选点；"
    " 请改用 scripts/run_md_sampling.py 生成 round_xxx_md_frame_manifest.json，"
    " 再用 scripts/select_md_frames.py 选下一轮样本。"
)