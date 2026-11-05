# 象棋训练素材 / Xiangqi training materials

为 SC3336 摄像头 + RV1106 象棋识别准备的训练素材、标注与模型交接仓库。现已提供 **v3 本机场景模型上机测试版**；其余章节保留对应素材包的交接记录。

## 2026-11-05 v3 模型上机测试版

- [下载 RV1106 模型：xiangqi14-local-v3-rv1106.rknn](https://github.com/lst92991-eng/xiangqi-training-materials-2026-11-04/releases/download/v2026.11.05-model-v3/xiangqi14-local-v3-rv1106.rknn)
- [下载完整模型包：PT / ONNX / RKNN / 参数](https://github.com/lst92991-eng/xiangqi-training-materials-2026-11-04/releases/download/v2026.11.05-model-v3/xiangqi-model-v3-20261105.zip)
- [Release 与校验文件](https://github.com/lst92991-eng/xiangqi-training-materials-2026-11-04/releases/tag/v2026.11.05-model-v3) · [上机参数、验证结果与限制](docs/model-v3.md)

沿用 YOLOv5s/ReLU、RGB 640×640、红黑14类和 RKNN Toolkit2 / 板端运行时 1.6.0 配套接口。`.pt` 和 `.onnx` 在完整模型包中；RV1106 NPU 使用 `.rknn`。

本次15帧原图各重复10轮，FP32及量化模拟均无错认、漏检、额外框；扩大到模糊、拖影、缩小和组合扰动后仍有错误。**这是供上机复测的候选模型，未完成本次新权重的RV1106实板验收，也不保证任意场景100%正确。** 原始补充包中的52处黑将/黑象对调标注已在训练副本中修正，[修改清单](docs/model-v3-label-corrections.json)保留，原数据Release未覆盖。

## 2026-11-05 本机实拍补充包

[下载实拍补充包（约 191 MB）](https://github.com/lst92991-eng/xiangqi-training-materials-2026-11-04/releases/tag/v2026.11.05-local-data)：三段 SC3336 录像、688 张候选图；其中 26 张 / 832 个框经助手视觉复核，提供小型 YOLO14 基准（train 19 / val 3 / test 4）、本地标注审核工具和微调交接说明。**688 张不等于 688 个独立有效局面，未审核草稿不能直接训练。** 此素材包发布时未训练新权重；后续v3模型及标注纠错见上节。

解压后先读 `README_训练交接.md`，运行 `python 05_tools/configure_paths.py` 生成本机路径。新包单独下载，下面的 `download_dataset.py` 仍下载 2026-11-04 公共大数据包。素材交接时的排查记录为：原模型同帧 ONNX / NPU 的 30 对检测中有 29 对类别一致，主要错分类在浮点模型里已存在，当时尚未启动新训练。后续微调结果以本页v3模型章节为准。

## 另一台电脑下载

需要 Git 和 Python 3.9+，下载器仅使用 Python 标准库，不需要登录 GitHub。

```bash
git clone https://github.com/lst92991-eng/xiangqi-training-materials-2026-11-04.git
cd xiangqi-training-materials-2026-11-04
python download_dataset.py
```

Linux 中若 Python 命令为 `python3`，相应替换即可。断网后重跑相同命令，已校验的分卷会复用，未完成分卷尝试断点续传。预留约 8 GB 空闲空间用于分卷、合并 ZIP 和解压后的文件。

脚本会下载三个 Release 分卷，分别验证 SHA256，合并并校验完整 ZIP，解压到 `data/`，然后自动生成适合当前电脑的 `data.local.yaml`。**`git clone` / `git pull` 本身只获取说明、清单和脚本；素材由上述下载命令获取。**

不运行脚本也可以从 [Release 页面](https://github.com/lst92991-eng/xiangqi-training-materials-2026-11-04/releases/tag/v2026.11.04) 下载三个 `part` 文件，使用仓库的下载器放入缓存后校验合并。可通过 `--output`、`--cache` 改变存储位置；`--download-only` 只生成完整 ZIP。

## 数据规模

| 项目 | 数量 |
| --- | ---: |
| 已转换为 14 类 YOLO 格式 | 10,094 张，包含源数据增强 |
| 推荐清单 | 9,187 张 / 248,117 个棋子框 |
| 训练 / 验证 / 测试 | 9,066 / 67 / 54 张 |
| 备用 MyRobot 原始导出 | 1,488 张，含镜像增强，未加入推荐清单 |
| 当前摄像头待人工标注 | 32 张候选全图及 32 张对应裁剪图，来自同一次录像 |

主数据来源为 Wood 8,032、FPT 1,645、Viktor 200，加上剔除一张已知错标后的旧数据 217。不能把增强数量或相邻视频帧数视为同等数量的独立实拍局面。

已完成逐图解码、边界与类别检查、精确像素重复处理和可识别拍摄日期分组。推荐清单排除 906 张留出拍摄日期的训练增强图及 1 张重复图。源标注只做了代表性视觉抽查，未逐框人工复标；公共测试集较小，仍需独立的当前摄像头标注集检验实际效果。

类别 ID 固定为 `kabnrcpKABNRCP`：黑将、士、象、马、车、炮、卒；红帅、仕、相、马、车、炮、兵。不要重新随机划分全部 images 文件夹。

## 训练交接

- [详细训练说明](docs/training-guide.zh-CN.md)
- [数据质量与逐类数量](docs/data-quality.zh-CN.md)
- [类别表](docs/classes.csv)
- [发布文件哈希与下载地址](release-manifest.json)

训练使用下载器打印的 `08_YOLO14_主数据/data.local.yaml`，沿用已有 airockchip YOLOv5s / ReLU 框架和固定 anchors。随包已有 portable.pt、原 RKNN、训练超参数、转换脚本和许可证。不要把当前 .pt 直接当新版 Ultralytics 通用权重。现有板端适配 RKNN Toolkit2 1.6.0，训练后需按该接口重新导出、量化并测试。

`tools/` 是交接脚本的可浏览副本。操作真实数据时运行解压包的 `04_标注与组集/` 中的脚本，它们依赖包内目录结构。新录制素材需要人工标注，当前模型预测不作为真值。此仓库不会自动启动训练。

## 来源、许可与改动

| 数据 | 原始项目 | 许可 |
| --- | --- | --- |
| Wood | [project-t4pwb / chess v6](https://universe.roboflow.com/project-t4pwb/chess-4b8i3/dataset/6) | CC BY 4.0 |
| FPT | [FINALTEST / Chinese Chess FPT v5](https://universe.roboflow.com/finaltest-lqish/chinese-chess-fpt/dataset/5) | CC BY 4.0 |
| Viktor | [Viktor Ng / Chinese Chess v1](https://universe.roboflow.com/viktor-ng/chinese-chess-rtpmq/dataset/1)，通过 [Kaggle 镜像](https://www.kaggle.com/datasets/palmerhuy/xiangqidatasetyolov8) 获取 | 保留原 CC BY 4.0；不以镜像许可覆盖 |
| MyRobot（备用） | [myrobot-wuh2o / Chess-Robot-Pose v8](https://universe.roboflow.com/myrobot-wuh2o/chess-robot-pose/dataset/8) | CC BY 4.0 |

本次处理包括 COCO→YOLO 转换、统一 14 类、移除 intersection 标签、排除已知错标、按拍摄日期重分组和精确去重。原作者说明、原 COCO 标注、源包 SHA256 和逐图溯源均在下载包内保留。CC BY 4.0 许可：https://creativecommons.org/licenses/by/4.0/ 。

这是混合来源交接包，不对全部文件统一改许可。旧数据、模型和框架的许可及来源说明见 [licenses/](licenses/) 与解压包的 `05_现有模型与转换约定/`。本项目自采素材和本次新写脚本由仓库所有者公开供本项目训练使用；其他用途如无明确许可，请联系仓库所有者。
