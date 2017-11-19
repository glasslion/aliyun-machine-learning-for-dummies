# 阿里云 ECS 机器学习懒人包

## DEMO
[使用文档](https://glasslion.github.io/aliyun-machine-learning-for-dummies/)

## 准备工作
本项目能帮助你在阿里云上全自动地创建、启动、安装、配置销毁用于机器学习的云服务器（ECS）实例。

在开始前， 还有些准备工作要做。 首先， 请确保你的阿里云账户余额大于 100元， 否则你将无法购买竞价实例。

### 配置 阿里云 access key
出于安全考虑, 本项目不会把阿里云的 Access ID 和 Access Key 保存到配置文件里去, 如果你不想要在每次创建/删除实例时手动输入密码, 可以将 access key设置在 `ALIYUN_ACCESS_KEY_ID` 和 `ALIYUN_ACCESS_KEY_SECRET` 两个环境变量里。

至于如何获取access key, 可以参考这篇教程: [如何获取Access ID和Access Key](https://help.aliyun.com/knowledge_detail/38738.html)

### 创建安全组

阿里云的默认安全组规则只开放了 22 和 3389 端口访问。 为了通过公网访问 Jupyter Notebook, 至少还需要再开放一个端口， 本项目里 Notebook 使用的是 8888 端口。

你需要进入阿里云的管理控制台， 创建一个新的安全组， 然后添加一条*入方向*的安全规则 。 *端口范围* 为 `8888/8888`。 *授权对象*为 `0.0.0.0/0`。 具体步骤可以参考这个教程: [添加安全组规则](https://help.aliyun.com/document_detail/25471.html)

注意: 安全组是和阿里云的[地域](https://help.aliyun.com/document_detail/40654.html?spm=5176.doc53090.2.9.sHPohS)绑定的, 香港的 ECS 只能使用香港的安全组, 不能使用美国的安全组.

### ECS 实例类型的选择
ECS 支持多种不同类型的实例， 但其中大部分并不适合用来跑机器学习。即便是那些被归类为计算型(即ecs.sn1)的主机, 也只是CPU比较强劲，用来做深入学习并没有多大优势。

在阿里云上。真正适合跑深度学习的主机是被归类在**异构计算**这个类别下。 这类主机不仅 CPU, 内存配置较高， 还搭载了性能强劲的<del>战术核</del>显卡, 非常适合用来做深度学习。 这其中又以 *GN5* 型最适合个人开发者(其实 GN4 也不错， 但现在基本买不到 GN4型的主机了)。

以 GN5 系列里配置最低的规格 *ecs.gn5-c4g1.xlarge* 为例， 它配备了4*2.5GHz的 CPU, 30G 内存 和 1块 NVIDIA P100 GPU。

在 **计费方式** 方面， 强烈推荐使用**竞价实例** 这一付费方式。 以*美国西部1区* 的 *ecs.gn5-c4g1.xlarge* 为例， 若使用按量付费模式， 每小时的价格为 ￥11.916， 而竞价实例模式， 每小时的价格尽为 ￥1.224。(注: 实例的价格会不断浮动， 请以阿里云官网的实时价格为准) 差别感人。

至于实例所属的**地域**， 建议选择**国外**。 由于不可描述的原因， 机器学习常用到的一些库， 数据集， 在国内网络下无法下载或下载速度极慢。 使用国外的主机可以直接规避这些问题。

### 添加 SSH Key
你还需要在阿里云控制台导入你本机的 SSH 公钥(一般为 ~/.ssh/id_rsa.pub)。 具体步骤可以参考这个教程: [导入 SSH 密钥对](https://help.aliyun.com/document_detail/51794.html?spm=5176.doc25471.6.706.Jn8xir)

本项目的自动化脚本在创建实例时， 会选择你所指定的 SSH key。 实例创建完成后， 就能通过 ssh 登录到主机了。

### 添加 Git(SSH) Key
你需要在 `playbook/tools/files/` 目录下添加一对 SSH 公私钥。 这对公钥主要是为了方便向 Github 上 push。

### 磁盘和快照
ECS 实例会自带一块系统盘和数据盘， 但这两块盘会随着ECS实例的删除而被同时释放。 为了持久化数据， 我采用的是再额外挂载一块数据盘的方式。 这块数据盘可以独立于ECS实例存在。 平时的操作都应在这块磁盘上进行（挂载在 `/mnt/ml` 目录下）。

当然， 你还可以把这块数据盘保存为快照来进一步节省费用。
运行 `start_instance.py` 时，在交互模式下， 你有3种选项可以选择:
1. 创建一块全新的数据盘(一般只有首次运行时， 才会用到)
2. 使用一块现有的数据盘(会列出你账户下所有的数据盘，供你选择)
3. 使用一个现有的磁盘快照来创建一个新的数据盘(会给出你的快照列表)
类似的， 在运行 `delete_instance.py` 销毁实例时， 你可以选择是否为当前的数据盘创建快照?


### Jupyter Notebook
本项目默认的 Jupyter Notebook 端口为 8888。 为了安全， Notebook 只开放了通过 https 的方式来访问, 即 `https://<公网 ip>:8888/`。 由于 HTTPS 使用的是自签名证书， 首次访问时，浏览器会有相应的警告。

Jupyter Notebook 应当被配置为通过密码认证后才能访问。`playbook/roles/libs/files/` 目录下有个 `jupyter_notebook_config.py.example`样例配置文件。 将这个文件重命名为 `jupyter_notebook_config.py`, **并替换其中的密码哈希**即可。 你可以参考 Jupyter 文档 [Preparing a hashed password](http://jupyter-notebook.readthedocs.io/en/stable/public_server.html#Preparing-a-hashed-password) 来设置你自己的哈希。注意，尽管 `jupyter_notebook_config.py` 里的密码是哈希过的， 你仍然应避免把它泄漏给其他人， 事实上， 本项目已经把 它加入到 .gitignore 中了。

## 使用指南

### 创建实例

第一次运行 `start_instance.py` 时，应使用交互模式, 即 `python start_instance.py -i`。 在交互模式下， 它会引导你选择、配置实例的各个参数， 例如区域，规格、安全组 ..., 并保存配置到 `config.json`。 再次运行时， 如果使用和之前一样的配置， 就不用再重复配置了。

### 销毁实例

### 系统配置和常用机器学习包的安装
实例的配置是通过 [ansible](https://www.ansible.com/) 来完成的。 进入 `playbook` 目录， 运行 `ansible-playbook ecs-gpu-instance.yml` 即可开始自动配置实例， 全程不需要人工干预。 (`start_instance.py` 在运行完成后, 会自动把新生成的实例的 ip 地址写入到 `playbook/hosts` 文件中)。

这个 playbook 里大致做了下面几件事：
- 创建了一个普通用户(用户名： `ml`) 以代替权限过大的 root 用户。你可以通过 `ssh ml@<server ip>` 的方式登录为整个用户。 该用户可以通过 sudo 获取 root 权限。
- 分区、格式化并挂载实例的两块数据盘。
- 安装配置 git, tmux, htop, iotop, unzip 等常用工具
- 卸载 Ubuntu 默认的显卡驱动(nouveau), 下载、安装 Nvidia 的官方驱动。(使用的是 阿里云 GN5系列所对应的 P100 GPU 的驱动， 故果你使用其他类型的实例，请确保)
- 下载、安装和配置 CUDA 8.0
- 安装和配置 cuDNN。 由于 Nvidia 不提供 cuDNN 的公开下载地址， 你需要在 Nvidia 官网上用帐号登录后， 下载 libcudnn5.deb， libcudnn5-dev.deb， libcudnn5-doc.deb 三个包， 放到 `/mnt/ml/cache/` 目录（数据盘）下。
- 安装 anaconda, 并创建一个名为 `py36` 的 conda 环境。
- 安装 tensorflow, mxnet, pytorch, theano, jupyter notebok 等机器学习常用的包。


以上操作都是 *幂等* 的。 重复执行不会产生副作用。 例如格式化磁盘， 只有检测到磁盘之前没有被格式化过，才会执行。


## 和 AWS EC2 对比
AWS 上和 阿里云 GN5 比较接近的是 [P2](https://aws.amazon.com/ec2/instance-types/p2/) 实例。使用的是 NVidia Tesla K80 显卡。 在性价比方面还是弱于阿里云的。

AWS 当然也有其优势的地方。 AWS EC2 实例在停机后就只收取磁盘费用， 而阿里云要在实例删除后才停止收费。 此外 AWS 提供了 Amazon Machine Image (AMI)， 即专为机器学习定制的系统镜像， 简化了 NVidia 驱动和 CUDA 的安装。


## 参考资料
- [Set up an GPU instance (p2.xlarge: Ubuntu 16.04+k 80 GPU) for deep learning on AWS](https://medium.com/@rogerxujiang/setting-up-a-gpu-instance-for-deep-learning-on-aws-795343e16e44)
- [Ansible 进阶技巧](https://www.ibm.com/developerworks/cn/linux/1608_lih_ansible/index.html)
- [Tips for Running TensorFlow with GPU Support on AWS](http://mortada.net/tips-for-running-tensorflow-with-gpu-support-on-aws.html)
- [ec2-gpu-instance](https://github.com/equialgo/ec2-gpu-instance)
