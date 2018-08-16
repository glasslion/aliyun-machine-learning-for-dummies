# -*- coding: utf-8 -*-
import os

import fabric
from fabric.api import cd, env, run, settings, task
from fabric.operations import put, prompt
from fabric.contrib.files import upload_template, exists as file_exists
import fabtools
from fabtools import require


env.user = 'root'
env.timeout = 120
env.connection_attempts = 3


@task
def bootstrap():
    require.users.user(
        'ml',
        shell='/bin/bash',
        ssh_public_keys=os.path.expanduser('~/.ssh/id_rsa.pub')
    )
    require.users.sudoer('ml')
    setup_ssh()
    setup_external_disks()
    setup_sys_packages()
    setup_nvdia_driver()
    optimize_gpu()
    setup_cuda()
    setup_conda()
    setup_pip()
    setup_jupyter()
    install_tensorflow()
    install_mxnet()
    install_pytorch()
    install_theano()
    install_keras()



# Help Functions:
# ---------------------------------------------------------

def download(url, dst):
    if fabric.contrib.files.exists(dst):
        return
    run('wget -nc {} -O {}'.format(url, dst))


def test_server_in_china():
    with settings(warn_only=True):
        out = run('curl -s -o /dev/null  -I -w "%{http_code}" https://www.google.com --connect-timeout 2 --max-time 2')
    return not out.startswith('302')


CONDA_PATH = '/mnt/ml/libs/anaconda3'


#  Tasks
# ---------------------------------------------------------

@task
def setup_ssh():
    with settings(user='ml'):
        if file_exists('~/.ssh/id_rsa.pub'):
            return
        require.files.directory(
            '~/.ssh', owner='ml', group='ml', mode='0700'
        )
        # Upload ssh key pair in the asserts directory, used by git push and ssh to other hosts
        fabric.operations.put(
            './assets/id_rsa.pub',
            '~/.ssh/id_rsa.pub'
        )
        fabric.operations.put(
            './assets/id_rsa',
            '~/.ssh/id_rsa',
            mode="600"
        )


@task
def setup_sys_packages():
    """
    Install and config common system packages, like vim, tmx, git ...
    machine learning interrelated packages are not included
    """
    fabtools.require.deb.uptodate_index(max_age={'day': 1})
    require.deb.packages([
        'htop',
        'vim',
        'unzip',
        'p7zip-full',
        'tree',
        'curl',
        'iftop',
        'iotop',
        'unrar-free',
        'bzip2',
        'bc',
        'ack-grep',
        'tmux',
        'git',
    ])

    # set vim as default editor
    run('update-alternatives --set editor /usr/bin/vim.basic')

    with settings(user='ml'):
        if file_exists('/home/ml/.tmux.conf'):
            return

        # tmux conf
        put('assets/tmux.conf', '~/.tmux.conf')

        # git config
        git_user = os.environ.get('GIT_USER') or prompt('Enter your git username')
        git_email = os.environ.get('GIT_EMAIL') or prompt('Enter your git email')
        upload_template(
            'assets/gitconfig',
            '~/.gitconfig',
            context={
                'git_user': git_user,
                'git_email': git_email,
            }
        )


@task
def mount_disks():
    """
    Mount external disk.
    It should be called after every restart
    """
    has_2_disks = file_exists('/dev/vdc')
    if has_2_disks:

        if not fabtools.disk.ismounted('/dev/vdb1'):
            fabtools.disk.mount('/dev/vdb1', '/mnt/data')
            fabtools.disk.mount('/dev/vdc1', '/mnt/ml')
    else:
        if not fabtools.disk.ismounted('/dev/vdb1'):
            fabtools.disk.mount('/dev/vdb1', '/mnt/ml')


@task
def setup_external_disks():
    require.files.directories(
        ['/mnt/ml', '/mnt/data'],
        owner='ml'
    )

    if not file_exists('/dev/vdb1'):
        run('parted -a optimal /dev/vdb mklabel gpt mkpart primary ext4 0% 100%')
        run('mkfs.ext4 /dev/vdb1')
    if file_exists('/dev/vdc') and not file_exists('/dev/vdc1'):
        run('parted -a optimal /dev/vdc mkpart primary ext4 0% 100%')
        run('mkfs.ext4 /dev/vdc1')

    mount_disks()

    require.files.directories(
        ['/mnt/ml/cache', '/mnt/ml/libs', '/mnt/ml/working'],
        owner='ml',
    )


@task
def setup_nvdia_driver():
    if not file_exists('/etc/modprobe.d/blacklist-nouveau.conf'):
        # Blacklist nouveau driver
        put(
            'assets/blacklist-nouveau.conf',
            '/etc/modprobe.d/blacklist-nouveau.conf'
        )
        # Disable the Kernel nouveau
        run('echo options nouveau modeset=0 | tee -a /etc/modprobe.d/nouveau-kms.conf')
        run('update-initramfs -u')
        run("shutdown -r +0")

    mount_disks()
    NVDIA_DRIVER_PATH = '/mnt/ml/cache/nvidia_driver.run'
    if not file_exists('/usr/bin/nvidia-smi'):
        with settings(user='ml'):
            download(
                'http://us.download.nvidia.com/tesla/390.30/NVIDIA-Linux-x86_64-390.30.run',
                NVDIA_DRIVER_PATH,
            )
        run('sh {} -q -a -n -s'.format(NVDIA_DRIVER_PATH))


@task
def setup_cuda():
    if fabric.contrib.files.exists('/usr/local/cuda/bin'):
        return
    require.deb.packages([
        'build-essential',
        'freeglut3-dev',
        'libx11-dev',
        'libxmu-dev',
        'libxi-dev',
        'libgl1-mesa-glx',
        'libglu1-mesa',
        'libglu1-mesa-dev',
    ])
    CUDA_DOWNLOAD_PATH = '/mnt/ml/cache/cuda.run'
    with settings(user='ml'):
        download(
            'https://developer.nvidia.com/compute/cuda/9.1/Prod/local_installers/cuda_9.1.85_387.26_linux',
            CUDA_DOWNLOAD_PATH,
        )

    run('sh {} -silent'.format(CUDA_DOWNLOAD_PATH))
    # ADD cuda to PATH bashrc
    with settings(user='ml'):
        for line in [
            "export PATH=$PATH:/usr/local/cuda/bin",
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64",
            "export CUDA_ROOT=/usr/local/cuda",
        ]:
            fabric.contrib.files.append(
                '~/.bashrc', line
            )
    run("shutdown -r +0")
    mount_disks()


@task
def optimize_gpu():
    # Optmize P2 according to http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/accelerated-computing-instances.html#optimize_gpu
    # Configure the GPU settings to be persistent
    run('nvidia-smi -pm 1')
    # Disable the autoboost feature for all GPUs on the instance.
    run('nvidia-smi --auto-boost-default=0')
    # Set all GPU clock speeds to their maximum frequency.
    # run('nvidia-smi -ac 715,1328')


@task
def setup_conda():
    CONDA_DOWNLOAD_PATH = '/mnt/ml/cache/anaconda3.sh'

    with settings(user='ml'):
        in_china = test_server_in_china()
        if in_china:
            conda_url = 'https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-5.0.1-Linux-x86_64.sh'
        else:
            conda_url = 'https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh'
        download(conda_url, CONDA_DOWNLOAD_PATH)
        run('bash {} -b -p {}'.format(
            CONDA_DOWNLOAD_PATH, CONDA_PATH
        ))

        upload_template(
            'assets/condarc',
            '~/.condarc',
            use_jinja=True,
            context={
                'in_china': in_china,
            }
        )

        fabric.contrib.files.append(
            '~/.bashrc',
            'export PATH={}/bin:$PATH'.format(CONDA_PATH)
        )
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('./conda update conda -y --force')


@task
def setup_jupyter():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            # ssl key
            run('openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout ~/.jupyter/mykey.key -out ~/.jupyter/mycert.pem -subj  "/C=NL"')

        require.files.directory('~/.jupyter')
        fabric.operations.put(
           'assets/jupyter_notebook_config.py',
            '~/.jupyter/jupyter_notebook_config.py'
        )


@task
def setup_pip():
    with settings(user='ml'):
        require.files.directory('/home/ml/.pip')
        in_china = test_server_in_china()
        upload_template(
            'assets/pip.conf',
            '~/.pip/pip.conf',
            use_jinja=True,
            context={
                'in_china': in_china,
            }
        )

@task
def install_tensorflow():
    in_china = test_server_in_china()
    if in_china:
        tensorflow_url = 'https://mirrors.tuna.tsinghua.edu.cn/tensorflow/linux/gpu/tensorflow_gpu-1.4.0-cp36-cp36m-linux_x86_64.whl'
    else:
        tensorflow_url = 'https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-1.4.0-cp36-cp36m-linux_x86_64.whl'
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('./pip install {}'.format(tensorflow_url))
            run('./pip install tensorboard')


@task
def install_mxnet():
    # Install mxnet dependences
    require.deb.packages([
        'build-essential',
        'libatlas-base-dev',
        'liblapack-dev',
        'libopencv-dev',
        'graphviz',
    ])
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('./pip install --pre mxnet-cu80')
            run('./pip install --pre graphviz')

@task
def install_pytorch():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('./conda install -y pytorch torchvision -c pytorch')

@task
def install_theano():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('./conda install -y --no-update-deps theano pygpu')

        fabric.operations.put(
            'assets/theanorc',
                '~/.theanorc'
        )

@task
def install_keras():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('./pip install keras')
            require.files.directory('/home/ml/.keras')

            backend = prompt('Chhoose your backend, tensorflow or theano?[th|tf]')
            upload_template(
                'assets/keras.json', '~/.keras/keras.json',
                use_jinja=True,
                context={
                    'backend': backend,
                }
            )


@task
def install_ossutil():
    with cd('/usr/local/bin'):
        url  = 'http://docs-aliyun.cn-hangzhou.oss.aliyun-inc.com/assets/attach/50452/cn_zh/1516454058701/ossutil64?spm=a2c4g.11186623.2.6.FLcLvd'
        run('wget {} -O ossutil'.format(url))
        run('chmod a+x ossutil')