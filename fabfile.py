# -*- coding: utf-8 -*-
import os

import fabric
from fabric.api import cd, run, settings, task
from fabric.operations import put, prompt
from fabric.contrib.files import upload_template
import fabtools
from fabtools import require


@task
def bootstrap():
    require.users.user('ml')
    require.users.sudoer('ml')
    setup_ssh()
    setup_external_disks()
    setup_sys_packages()
    setup_nvdia_driver()
    optimize_gpu()
    setup_cuda()
    setup_conda()
    setup_jupyter()
    setup_pip()

def setup_ssh():
    require.files.directory(
        '~ml/.ssh', owner='ml', group='ml', mode='0700'
    )
    with settings(user='ml'):
        # Add current machine's public key to authorized_keys
        with open('~/.ssh/id_rsa.pub') as f:
            login_key = f.read()
        fabric.contrib.files.append(
            '.ssh/authorized_keys', login_key
        )
        require.files.file('~ml/.ssh/authorized_keys', mode='600')

        # Upload ssh key pair in the asserts directory, used by git push and ssh to other hosts
        fabric.operations.put(
            'assets/id_rsa.pub',
            '~ml/.ssh/id_rsa.pub'
        )
        fabric.operations.put(
            'assets/id_rsa',
            '~ml/.ssh/id_rsa',
            mode="600"
        )

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
        # tmux conf
        put('assets/tmux.conf', '~ml/.tmux.conf')

        # git config
        git_user = prompt('Enter your git username')
        git_email = prompt('Enter your git email')
        upload_template(
            'assets/gitconfig',
            '~ml/.gitconfig',
            context={
                'git_user': git_user,
                'git_email': git_email,
            }
        )

def setup_external_disks():
    require.files.directories(
        ['/mnt/ml', '/mnt/data'],
        owner='ml'
    )

    has_2_disks = fabric.contrib.files.exists('/dev/vdc')
    run('parted -a optimal /dev/vdb mkpart primary ext4 0% 100%')
    if has_2_disks:
        run('parted -a optimal /dev/vdc mkpart primary ext4 0% 100%')
        fabtools.disk.mount('/dev/vdb1', '/mnt/data')
        fabtools.disk.mount('/dev/vdc1', '/mnt/ml')
    else:
        fabtools.disk.mount('/dev/vdb1', '/mnt/ml')

    require.files.directories(
        ['/mnt/ml/cache', '/mnt/ml/lib', '/mnt/ml/working'],
        owner='ml',
    )

def download(url, dst):
    run('wget -nc {} -O {}'.format(url, dst))


def setup_nvdia_driver():
    # Blacklist nouveau driver
    put(
        'assets/blacklist-nouveau.conf',
        '/etc/modprobe.d/blacklist-nouveau.conf'
    )
    # Disable the Kernel nouveau
    run('echo options nouveau modeset=0 | tee -a /etc/modprobe.d/nouveau-kms.conf')
    run('update-initramfs -u')
    fabric.operations.reboot()
    NVDIA_DRIVER_PATH = '/mnt/ml/cache/nvdia_driver.run'
    if not fabric.contrib.files.exists(NVDIA_DRIVER_PATH):
        with settings(user='ml'):
            download(
                'http://us.download.nvidia.com/tesla/384.81/NVIDIA-Linux-x86_64-384.81.run',
                NVDIA_DRIVER_PATH,
            )
        run('sh {} -q -a -n -s'.format(NVDIA_DRIVER_PATH))

def setup_cuda():
    if fabric.contrib.files.exists('/usr/local/cuda/bin'):
        return
    CUDA_DOWNLOAD_PATH = '/mnt/ml/cache/cuda.deb'
    with settings(user='ml'):
        download(
            'https://developer.nvidia.com/compute/cuda/8.0/Prod2/local_installers/cuda-repo-ubuntu1604-8-0-local-ga2_8.0.61-1_amd64-deb',
            CUDA_DOWNLOAD_PATH,
        )

    run('dpkg - i {}'.format(CUDA_DOWNLOAD_PATH))
    fabtools.require.deb.uptodate_index()
    require.deb.packages([
        'build-essential',
        'dkms',
        'linux-generic',
        'cuda',
    ])

    # ADD cuda to PATH bashrc
    with settings(user='ml'):
        for line in [
            "export PATH=$PATH:/usr/local/cuda/bin",
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64",
            "export CUDA_ROOT=/usr/local/cuda",
        ]:
            fabric.contrib.files.append(
                '~ml/.bashrc', line
            )


@task
def optimize_gpu():
    # Optmize P2 according to http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/accelerated-computing-instances.html#optimize_gpu
    # Configure the GPU settings to be persistent
    run('nvidia-smi -pm 1')
    # Disable the autoboost feature for all GPUs on the instance.
    run('nvidia-smi --auto-boost-default=0')
    # Set all GPU clock speeds to their maximum frequency.
    # run('nvidia-smi -ac 715,1328')


def test_server_in_china():
    out = run('curl -s -o /dev/null  -I -w "%{http_code}" https://www.google.com --connect-timeout 2 --max-time 2')
    return out.startswith('302')


CONDA_PATH = '/mnt/ml/libs/anaconda3'


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
            '~ml/.condarc',
            use_jinja=True,
            context={
                'in_china': in_china,
            }
        )

        fabric.contrib.files.append(
            '~ml/.bashrc',
            'export PATH={}/bin:$PATH'.format(CONDA_PATH)
        )
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('conda update conda -y --force')
            run('conda create -y -n py36 python=3.6')


@task
def setup_jupyter():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            # Install nb_conda
            run('conda install -y jupyter nb_conda nb_conda_kernels -c conda-forge')
            # Enable conda kernels
            run('python -m nb_conda_kernels.install --enable')
            # Install notedown
            run('python install notedown')
            # ssl key
            run('openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout ~/.jupyter/mykey.key -out ~/.jupyter/mycert.pem -subj  "/C=NL"')

        require.files.directory('~ml/.jupyter')
        fabric.operations.put(
           'assets/jupyter_notebook_config.py',
            '~ml/.jupyter/jupyter_notebook_config.py'
        )


@task
def setup_pip():
    with settings(user='ml'):
        require.files.directory('~ml/.pip')
        in_china = test_server_in_china()
        upload_template(
            'assets/pip.conf',
            '~ml/.pip/pip.conf',
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
            run('pip install {}'.format(tensorflow_url))
            run('pip install tensorboard')


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
            run('pip install --pre mxnet-cu80')
            run('pip install --pre graphviz')

@task
def install_pytorch():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('conda install pytorch torchvision -c pytorch')

@task
def install_theano():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('conda install install -y --no-update-deps theano pygpu')

        fabric.operations.put(
            'assets/theanorc',
                '~ml/.theanorc'
        )

@task
def install_keras():
    with settings(user='ml'):
        with cd(os.path.join(CONDA_PATH, 'bin')):
            run('pip install keras')
            require.files.directory('~ml/.keras')

            backend = prompt('Chhoose your backend, tensorflow or theano?[th|tf]')
            upload_template(
                'assets/keras.json', '~ml/.keras/keras.json',
                use_jinja=True,
                context={
                    'backend': backend,
                }
            )

