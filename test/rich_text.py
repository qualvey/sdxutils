
from openpyxl.styles    import Font
from openpyxl.cell.text import InlineFont 
from openpyxl.cell.rich_text import TextBlock, CellRichText

from openpyxl                import load_workbook
#
'''
测试结果表示，
用InlineFont直接写出来返回的对象可以使用
用InlineFont包裹Font对象之后的对象则不生效

'''
#

workbook = load_workbook('./2025年日报表.xlsx')
worksheet = workbook.active

yahei_inline = InlineFont(rFont='Microsoft YaHei', # Font name
                         sz=22,           # in 1/144 in. (1/2 point) units, must be integer
                         charset=None,    # character set (0 to 255), less required with UTF-8
                         family=None,     # Font family
                         b=True,          # Bold (True/False)
                         i=None,          # Italics (True/False)
                         strike=None,     # strikethrough
                         outline=None,
                         shadow=None,
                         condense=None,
                         extend=None,
                         u=None,
                         vertAlign=None,
                         scheme=None,
                         color='00FF0000'
                         )

inline_font = InlineFont(rFont='Calibri',
            sz=5,
            color='00FF0000')
red = InlineFont(color='00FF0000')
b = TextBlock

rich_string = CellRichText(
    b(red, f'aaaa'),
    b(yahei_inline, f'bbbb'),
    b(red, f'xxx'),
    b(inline_font,"red?")
    )

worksheet['G41'] = rich_string
worksheet['G42'] = "ddddd"
workbook.save('./rich.xlsx')


#rich_string = CellRichText(
#    b(inline_yahei_red_8, f'{index}'),
#    b(inline_yahei, f'{reason:<{max_reason_length + padding_length}}:'),
#    b(inline_yahei_red_8, f'{total}')
#    )
