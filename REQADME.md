## 使用须知
创建实例前， 请确保你的阿里云账户余额大于 100元， 否则将无法购买竞价实例。


[如何获取Access ID和Access Key](https://help.aliyun.com/knowledge_detail/38738.html)
[地域ID(Region ID)列表](https://help.aliyun.com/document_detail/40654.html?spm=5176.doc53090.2.9.sHPohS)

### 安全组
阿里云的默认安全组规则只开放了 22 和 3389 端口访问。 为了通过公网访问 Jupyter Notebook, 至少还需要再开放一个端口， 本项目使用的是 8888 端口。
你需要进入阿里云的管理控制台， 创建一个新的安全组， 然后添加一条*入方向*的安全规则 。 *端口范围* 为 `8888/8888`。 *授权对象*为 `0.0.0.0/0`。

## 磁盘和镜像
磁盘格式化

## AWS
p2.xlarge NVIDIA Corporation GK210GL [Tesla K80]

## Notebook
本项目默认的 Jupyter Notebook 端口为 8888。



## 参考资料
- [Set up an GPU instance (p2.xlarge: Ubuntu 16.04+k 80 GPU) for deep learning on AWS](https://medium.com/@rogerxujiang/setting-up-a-gpu-instance-for-deep-learning-on-aws-795343e16e44)
- [Ansible 进阶技巧](https://www.ibm.com/developerworks/cn/linux/1608_lih_ansible/index.html)
- [Tips for Running TensorFlow with GPU Support on AWS](http://mortada.net/tips-for-running-tensorflow-with-gpu-support-on-aws.html)
