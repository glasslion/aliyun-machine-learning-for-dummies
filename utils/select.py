import time
import itertools

import click
import colorful

from .action import do_action


class BaseConfigParameterSelect(object):
    def __init__(self, config):
        self.config = config
        self.client = config.create_api_client()

    def show(self, refresh=False):
        if not refresh:
            click.echo(click.style('正在配置 ECS 实例的{} ...', fg='green').format(self.name))
            param = self.config.get(self.key)
            if param:
                msg = "检测到你上次所使用的{}是 {}, 是否保留这个设置， 还是重新选择? [保留 y/重选 n]".format(
                    self.name, click.style(param, fg="magenta")
                )
                answer = click.prompt(msg, default='y').lower()
                if answer == 'y':
                    return param

        items = self.get_items()
        if len(items)==0:
            self.fix_empty_items()
            time.sleep(1)
            return self.show(refresh=True)

        formatted = self.format_items(items)

        idx = click.prompt(formatted, type=int, default=-1, show_default=False)
        if idx == -1:
            return self.show(refresh=True)

        param = items[idx][self.item_key]
        self.config.set(self.key, param)
        self.handle_selected_item(items[idx])

    def set_request_parameters(self, request):
        pass

    def handle_selected_item(self, item):
        pass

    def fix_empty_items(self):
        raise NotImplementedError('Empty Select List !!!')

    def get_items(self):
        """
        Get a list of items for select
        """
        request = self.request_cls()
        self.set_request_parameters(request)
        result = do_action(self.client, request)

        items = self.items_getter(result)

        if getattr(self, 'select_sorting', None):
            items.sort(key=lambda x: x[self.select_sorting])

        return items

    def format_items(self,items):
        lines = [
            '[{}] - {}'.format(idx, self.select_item_formatter(item))
             for idx, item in enumerate(items)
        ]
        select_list = '\n'.join(color_text(lines))
        formatted = '可选的 {}:\n{}\n请选择实例的 {}（序号） 回车来重新刷新本菜单'.format(
            self.name, select_list, self.name)
        return formatted


def color_text(lines):
    colors = [
        colorful.yellow, colorful.orange, colorful.magenta,
        colorful.green, colorful.blue, colorful.cyan,
    ]

    colored = [color(line) for line, color in zip(lines, itertools.cycle(colors))]
    return [str(line) for line in colored]
