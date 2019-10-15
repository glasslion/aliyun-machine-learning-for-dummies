import itertools
import colorful

def test_color():
    colorful.use_true_colors()
    colorful.use_style('monokai')

    cnames = ['blue', 'green', 'yellow', 'brown', 'darkGray', 'magenta', 'gray', 'lightGray', 'lightGhostWhite', 'lightOrange', 'brownGray', 'orange', 'ghostWhite', 'purple', 'seaGreen']

    colors = [getattr(colorful, cname) for cname in cnames]
    styles = [c.style for c in colors]
    lines = ['demo']*20
    colored = [color(line) for line, color in zip(lines, itertools.cycle(colors))]
    cls =  [str(line) for line in colored]
    for c in cls:
        print(c)
