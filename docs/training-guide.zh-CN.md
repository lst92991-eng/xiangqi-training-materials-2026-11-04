# 象棋训练数据交接（2026-11-04）

本包用于到另一台电脑训练，未在当前电脑启动训练，也没有更换正在测试的模型。请先查看 `数据质量报告.md` 的最终数量和检查结果。

## 从哪里开始

1. 将整个包解压到训练电脑。建议使用短路径，如 `D:/xiangqi_data` 或 `/data/xiangqi_data`。
2. 运行 `python 04_标注与组集/configure_paths.py`，它只生成本机路径，不启动训练。
3. 训练数据参数使用 `08_YOLO14_主数据/data.local.yaml`。**必须使用随包 train/val/test 清单，不要对 images 文件夹重新随机划分，也不要把全部图片一股脑加入训练。**
4. 主数据已完成 COCO→YOLO 检测框转换、14 类映射、逐图解码、结构检查、已知错标剔除和精确像素去重处理。源数据标注仍需抽查；这不等于每一个框均经过人工复标。
5. 新拍的本机素材在 `01_本机实拍`，暂不在训练清单内。裁剪图与全图是一一对应的不同视图，不是两倍的新场景。

## 本包内容

| 目录 | 用途 |
| --- | --- |
| 01_本机实拍 | 约 64 秒 SC3336 原视频、32 张候选全图、32 张对应棋盘裁剪图、采集记录；部分有手部遮挡，待人工标注 |
| 02_旧数据原包 | 原 218 张数据 ZIP，保持原样；已知一张错误标签不进入主数据 |
| 03_相似公开实拍 | 早期搜索和风格对照，4 张实拍现已由完整 FPT 集替代，不重复加入；游戏截图排除 |
| 04_标注与组集 | 类别表、人工审核表、可重建转换脚本、路径配置和结构验证脚本 |
| 05_现有模型与转换约定 | 用户原有 portable.pt、RKNN、导出脚本、训练超参数和来源许可 |
| 06_现状与证据 | 现有模型测试与误识别记录、数据抽查图；叠框截图不是训练图片 |
| 07_完整外部数据集 | FPT/Viktor 原始导出、含镜像增强的 MyRobot 备用原包及来源说明 |
| 08_YOLO14_主数据 | 已转换的主数据、推荐分组清单、逐图清单、原 COCO 标注及来源说明、核验结果 |

木质棋具完整原始 ZIP 体积约 1.51 GB，下载后已校验。其图片和原 COCO 元数据均已纳入 08 目录，不再在交付包内重复保存这一大 ZIP；原 ZIP 仍在本机 Downloads。重建时通过 `build_public_dataset.py --wood 原ZIP路径 --output 新目录` 指定。

## 来源和许可

以下三个主来源与一个备用来源的导出说明均声明 **CC BY 4.0**。保留作者/项目、链接和原说明；本次更改为类别映射、格式转换、边界舍入修正、排除、去重处理及重新划分。许可证参考：https://creativecommons.org/licenses/by/4.0/ 。不要把下载镜像的许可声明用于覆盖原始数据许可。

| 来源 | 原始文件规模 / 导出规模 | 取用方式 |
| --- | --- | --- |
| [project-t4pwb / chess v6](https://universe.roboflow.com/project-t4pwb/chess-4b8i3/dataset/6) | 3,320 / 8,032 | 主来源；木质圆棋、真实拍摄，训练导出包含旋转与亮度增强 |
| [FINALTEST / Chinese Chess FPT v5](https://universe.roboflow.com/finaltest-lqish/chinese-chess-fpt/dataset/5) | 685 / 1,645 | 主来源；实拍木棋，多尺度、方向和背景；包含裁剪、亮度、模糊增强 |
| [Viktor Ng / Chinese Chess v1](https://universe.roboflow.com/viktor-ng/chinese-chess-rtpmq/dataset/1) | 200 / 200 | 主来源；从 [Kaggle 镜像](https://www.kaggle.com/datasets/palmerhuy/xiangqidatasetyolov8) 下载，去除 intersection 类；同源镜像没有重复计数 |
| [MyRobot / Chess-Robot-Pose v8](https://universe.roboflow.com/myrobot-wuh2o/chess-robot-pose/dataset/8) | 620 / 1,488 | 仅备用原包；训练导出含水平/垂直镜像，会产生镜像汉字，未加入推荐主清单 |

原始文件数量不代表独立棋局；其中有相邻视频帧。导出数量包括数据增强，不能宣称是同等数量的新实拍。旧数据及模型的来源/许可证见 05 目录。

## 划分原则与测试局限

- 木质来源以文件名里的拍摄日期分组，同日左右摄像头及所有帧保持在同一集合；2026-07-11 用作验证，2026-07-15 用作测试，其余训练。
- FPT 以可识别拍摄日期分组；2026-06-05 验证，2026-06-10 测试，其余训练。
- 上述留出批次中，原导出 `train` 的增强图片保存在数据中以供追溯，但不加入任何推荐清单；验证/测试仅用原导出 valid/test 中的图片。
- 无法可靠识别拍摄批次的图片，以及旧数据和 Viktor 来源，全部只放训练集。因此旧的 22 张验证、22 张测试不能再作为本次独立测试依据。
- 已检查精确像素重复及已知拍摄分组；没有宣称消除了所有近似图、所有跨来源重复场景或全部标注错误。
- 公共数据验证成绩不能代替你这套 SC3336、棋具、位置和光照的现场成绩。还需要另一次独立实拍和人工标注作为现场验证/测试。

## 本机素材怎么标注

优先标注 01 目录的 `board_crops_unlabeled`。对清楚可辨的每枚棋子按整个棋子外缘画框，类别使用 04 目录的 classes.txt / classes.csv；不要只框汉字，也不要把识别不出的遮挡棋子凭模型猜成某一类。先排除严重模糊、无法可靠标注的图片；一张保留的图片应把所有目标棋子标完整。

人工完成后，在 `reviews.csv` 填写 label 相对路径、reviewer、reviewed=yes；该次采集全部保持 train 和原 group_id。没有棋子且确实作为负样本的图片才可以给空标签并填写 negative_confirmed=yes，未标注图片不能冒充负样本。

运行 `python 04_标注与组集/add_reviewed_local.py`，再运行 configure_paths.py。该导入是一次性的，避免重复追加。原公共数据 summary.json 保持基准统计，新加入数量记在 local_review_manifest.json。

## 到另一台电脑训练

为继续使用当前 RV1106 接口，沿用已有模型的框架：`airockchip/yolov5` 的 `rk_opt@v6.2.1`，固定提交 `23a20ef3e5fa648e765e4a70b30edbfd3aaf8c8c`，YOLOv5s / ReLU、640 输入、固定 anchors、`--noautoanchor`。不要把旧权重直接当作新版 Ultralytics 的通用权重加载。原项目转换工具和兼容补丁位于 05 目录，详见 SOURCES.original.md。

在匹配的 YOLOv5 源码目录中，下面是**供训练电脑手动运行**的示例；把各路径替换为该电脑实际绝对路径。batch-size 可按显存调整：

```text
python train.py --weights "包路径/05_现有模型与转换约定/xiangqi14-s-best-portable.pt" --cfg models/yolov5s.yaml --data "包路径/08_YOLO14_主数据/data.local.yaml" --hyp "包路径/05_现有模型与转换约定/model-tools/train-hyp.yaml" --imgsz 640 --batch-size 4 --epochs 150 --patience 30 --seed 42 --optimizer AdamW --noautoanchor --workers 2 --device 0 --project runs/train --name xiangqi14-expanded
```

随包原超参数已关闭水平/垂直镜像。主数据中已有增强，不宜仅为了扩大数量反复复制同一批帧。训练过程中重点看将/帅、士/仕、象/相、马、车、炮的逐类 precision/recall 和混淆矩阵，兵/卒准确并不代表其余类别已学好。

数量不足可能是原因之一，但字体、尺寸、角度、曝光、标注质量和类别分布也会影响结果。目前没有新训练结果，不能承诺本包训练后准确率。优先用已有权重微调并与原模型在**同一套独立现场标注集**比较。

训练完成请带回 best.pt、训练参数、逐类验证结果和混淆矩阵。后续仍需按现有 RKNN Toolkit2 1.6.0 / RV1106 运行时约定导出和量化，校准图应包含当前摄像头真实场景；不能将 .pt 直接改后缀当成 .rknn。

## 可追溯性

08 目录的 manifest.json 记录每张图片的来源成员名、原始父图、原划分、新划分、像素 SHA256 和类别统计；issues.json 记录排除/异常；source_archives.json 记录源包 SHA256。audit_previews 提供按类别排列的抽查图及对应索引。

根目录 SHA256SUMS.txt 用于文件传输核验。完成人工标注、路径配置或追加后，相关文件哈希自然会变化；保留原 ZIP 可随时回到本次交付基准。
