### 安装
本项目需要在类 Unix 环境下运行(Linux,MacOS ...), Windows 用户则推荐使用使用 Windows Subsystem for Linux(WSL)。

使用的 Python 版本为 Python 3。 由于阿里云 Python2 版的 SDK 有一些 bug， 目前要对 Python 2 的支持比较困难。
还在使用 Python 2 用户， 建议尽快升级。 Data science 社区在拥抱 Python 3 方面十分积极， 主流的库都早已支持 Python3。 像 Jupyter, Numpy 等库甚至都已经放弃或即将放弃对 Python 2 的支持。

```bash
cd aliyun-machine-learning-for-dummies

# 通过 pip 安装依赖`
pip install -r requirements.txt
```

### 创建实例
运行 `start_instance.py` 来创建和启动一个 实例。

```
python start_instance.py --help

Usage: start_instance.py [OPTIONS]

Options:
  -i, --interactive  Interactive mode，allow user to input/select ecs instance
                     parameters interactively
  --help             Show this message and exit.

```

运行时指定 `-i` 或 `--interactive` 参数， 就可以进入交互模式，在交互模式下， 它会引导你选择、配置实例的各个参数， 例如区域，规格、安全组 ... 并把你输入的各种配置保存到 `config.json` 文件中。
今后你如果想要再创建和上次一样的实例， 直接运行 `start_instance.py`， 就会使用 `config.json` 文件里的配置来创建实例了。

### 配置实例， 安装常用的机器学习框架、包

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

### 销毁实例

运行 `delete_instance.py` 来销毁你当前的实例。 在销毁时， 你可以选择为你的数据盘创建一个快照， 然后销毁数据盘。 今后创建实例时， 可以选择用这个快照来创建数据盘。快照的收费要比云盘便宜一些。