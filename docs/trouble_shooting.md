### 创建的系统盘镜像无法启动主机



### apt 源下载速度慢
阿里云的 ubuntu 主机默认会使用阿里云自己的 apt 源 (xxx.mirrors.cloud.aliyuncs.com)。 但我在使用过程中发现， 在某些国外节点上，对应的 apt 源下载速度很慢， 只有 100 多 k。 在使用 playbook 配置机器时， 就是发现会卡在安装 conda 这一步骤下很久, 因为 安装 conda 会用 apt 下载好几百MB数据。 这种情况下， 我们可以切回 ubuntu 官方源， 国外官方源下载速度很快， 基本在50MB/s 以上， 足够用了。