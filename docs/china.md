在之前的文档里， 已经建议大家优先使用阿里云海外的实例。 但有时海外的实例价格可能比国内高很多，或者是某些海外实例由于不可描述的原因在国内访问困难， 那么选择阿里云国内的实例也未尝不可。

在运行 playbook 时， 指定一个额外的参数 `china` (e.g. `ansible-playbook ecs-gpu-instance.yml -e china=1`)， 就会针对国内的网络环境做一些优化:

- 配置 pip 使用阿里云的[镜像](http://mirrors.aliyun.com/pypi/simple/)
- 配置 conda 使用清华大学的[镜像](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)
- 安装 tensorflow 时, 使用清华大学的[镜像](https://mirrors.tuna.tsinghua.edu.cn/help/tensorflow/)

这样可以极大地加快一些机器学习， 科学计算相关的库的安装速度。

### https 可能无法访问问题
国内部分运营商（例如上海电信) 会屏蔽通过 https 直连海外 ip。 打开 `jupyter_notebook_config.py` 注释掉以 `c.NotebookApp.certfile`, `c.NotebookApp.keyfile` 开头的两行， 即可让 Jupyter Notebbok 使用 http 而非 https 模式。