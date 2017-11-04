# 使用须知

## 准备工作

创建实例前， 请确保你的阿里云账户余额大于 100元， 否则将无法购买竞价实例。
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

## 添加 SSH Key
你还需要在阿里云控制台导入你本机的 SSH 公钥(一般为 ~/.ssh/id_rsa.pub)。 具体步骤可以参考这个教程: [导入 SSH 密钥对](https://help.aliyun.com/document_detail/51794.html?spm=5176.doc25471.6.706.Jn8xir)

本项目的自动化脚本在创建实例时， 会选择你所指定的 SSH key。 实例创建完成后， 就能通过 ssh 登录到主机了。


## 磁盘和镜像
磁盘格式化

## Notebook
本项目默认的 Jupyter Notebook 端口为 8888。 为了安全， Notebook 只开放了通过 https 的方式来访问, 即 `https://<公网 ip>:8888/`。
由于 HTTPS 使用的是自签名证书， 首次访问时，浏览器会有相应的警告。

## 和 AWS EC2 对比
p2.xlarge NVIDIA Corporation GK210GL [Tesla K80]




## 参考资料
- [Set up an GPU instance (p2.xlarge: Ubuntu 16.04+k 80 GPU) for deep learning on AWS](https://medium.com/@rogerxujiang/setting-up-a-gpu-instance-for-deep-learning-on-aws-795343e16e44)
- [Ansible 进阶技巧](https://www.ibm.com/developerworks/cn/linux/1608_lih_ansible/index.html)
- [Tips for Running TensorFlow with GPU Support on AWS](http://mortada.net/tips-for-running-tensorflow-with-gpu-support-on-aws.html)
