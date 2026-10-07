# 第三方来源与许可证

## 播放器

本包的播放器与自动绑定代码基于 [lTwTlol/Auto-live2D-beta](https://github.com/lTwTlol/Auto-live2D-beta)。项目根目录的 `LICENSE` 保留上游原文：MIT License，Copyright (c) 2026 hakoniwa。

上游 README 说明该项目基于 [852wa/Anime2.5DRig](https://github.com/852wa/Anime2.5DRig)，原始说明保留于 `docs/上游README.md`。

## PSD 解析

`lib/ag-psd.min.js` 为上游附带的 [ag-psd](https://github.com/Agamnentzar/ag-psd) PSD 解析库。它属于第三方代码，不是本分享包原创代码。官方 MIT 许可证及版权声明保留于 [licenses/ag-psd-MIT.txt](licenses/ag-psd-MIT.txt)，来源为 [官方 LICENSE](https://github.com/Agamnentzar/ag-psd/blob/master/LICENSE)。

## 图片拆层与运行时外部资源

- 图片拆层使用 See-Through，服务入口：https://modelscope.cn/studios/ljsabc/See-Through 。本包不包含该服务的模型权重或推理程序。
- 摄像头追踪入口在启用时会从 jsDelivr 加载 MediaPipe FaceMesh 文件；基础离线形象展示不需要它。本包没有将这些远程资源打包到本地。

## 本包素材

人物原始插画由 GPT 生成；分层 PSD、预览图片与视频由该插画经过拆层、修正和动态展示制作而来。智乃角色、插画、PSD、预览图片与视频是展示素材。它们不因为与代码放在同一目录，就自动获得代码的 MIT 授权。

分享整理与本次修改署名：奶龙大人sama；B站主页：https://space.bilibili.com/12723119 。保留上游作者、项目链接及许可证声明。
