from tools import  env
from openpyxl import load_workbook

path = f'{env.proj_dir}/et/0325市调表.xlsx'
save = f'{env.proj_dir}/et/lost.xlsx'

workbook = load_workbook(path)
worksheet = workbook.active

workbook.save(save)


