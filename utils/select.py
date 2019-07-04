import click
import time

from .action import do_action


class BaseConfigParameterSelect(object):
    def show(self, config, client=None):
        self.config = config
        click.echo(click.style('正在配置 ECS 实例的{} ...', fg='green').format(self.name))
        param = config.get(self.key)
        if param:
            msg = "检测到你上次所使用的{}是 {}, 是否保留这个设置， 还是重新选择? [保留 y/重选 n]".format(
                self.name, click.style(param, fg="magenta")
            )
            answer = click.prompt(msg, default='y').lower()
            if answer == 'y':
                return param

        request = self.request_cls()
        self.set_request_parameters(request)

        if client is None:
            client = config.create_api_client()
        self.client = client
        api_result = do_action(client, request)
        items = self.items_getter(api_result)
        if getattr(self, 'select_sorting', None):
            items.sort(key=lambda x: x[self.select_sorting])
        select_list = '\n'.join('[{}] - {}'.format(
            idx, self.select_item_formatter(item)
        ) for idx, item in enumerate(items))

        if len(select_list)==0:
            self.fix_empty_select_list()
            time.sleep(1)
            return self.show(config, client)

        msg = '可选的 {}:\n{}\n请选择实例的 {}（序号）'.format(self.name, select_list, self.name)
        idx = click.prompt(msg, type=int)
        param = items[idx][self.item_key]
        config.set(self.key, param)
        self.handle_selected_item(items[idx], config)

    def set_request_parameters(self, request):
        pass

    def handle_selected_item(self, item, config):
        pass

    def fix_empty_select_list(self):
        raise ValueError('Empty Select List !!!')