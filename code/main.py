import json
import os
import pprint
import classes.utils as ut
from classes.Color import Color
import cv2
import shutil
import warnings
from jinja2 import Environment, FileSystemLoader
import numpy as np
import subprocess
import re

warnings.simplefilter('ignore')

_PATH_CURRENT = os.path.dirname(__file__)
_PATH_TEMP = os.path.join(_PATH_CURRENT, "temp")
print(_PATH_CURRENT)

C_COLORS = {
	"c_blue":	"#2367cb",
}
FLG_KORAIL = False
FLG_SEOUL_METRO = True
companies = [
	"korail",
	"seoul_metro",
	"AREX",
	"DXLine",
	"incheon",
	]
shutil.rmtree(_PATH_TEMP)
os.mkdir(_PATH_TEMP)
for company in companies:
	print("####", company, "########")

	dat_path = os.path.join(_PATH_CURRENT, "..", "src", company)
	img_path = os.path.join(dat_path, "img")
	shutil.rmtree(dat_path)
	os.mkdir(dat_path)
	os.mkdir(img_path)

	jsons_path = os.path.join(_PATH_CURRENT, "designs", company)
	files = [
		os.path.join(jsons_path, f) for f in os.listdir(jsons_path) if os.path.isfile(os.path.join(jsons_path, f)) and os.path.splitext(f)[1] == ".json"
	]

	env = Environment(
		loader=FileSystemLoader(os.path.join(_PATH_CURRENT, "templates", company), encoding="utf-8"),
		trim_blocks=True
	)

	for file in files:
		with open(file, mode='r', encoding="utf-8") as f:
			datas = json.load(f)
			print("", os.path.basename(file))
			for data, index in zip(datas, range(len(datas))):
				name = data["name"].format(car="0")
				print("処理中", str(index), "/", str(len(datas)), name, end="", flush=True)
				for color in ["maincolor", "subcolor"]:
					if not(color) in data:
						data[color] = {"code": None}
					if "name" in data[color]:
						data[color]["code"] = C_COLORS[data[color]["name"]]

				maskImgs = {}
				outputImg = None

				parts = []
				if company in ["korail",] :
					parts = ["body", "face"]
				elif company in ["seoul_metro", "AREX", "DXLine", "incheon",] :
					parts = ["body"]

				for part in parts:
					masks = []
					for color, mask in [(data["maincolor"]["code"], "mainMask.png"), (data["subcolor"]["code"], "subMask.png")]:
						path = os.path.join(_PATH_CURRENT, "imgs", company, part, data[part], mask)
						if os.path.exists(path) and color:
							maskImg = ut.imread(path)
							maskImg = ut.multiplyColor(maskImg, Color(color))
							masks.append(maskImg)
					body = ut.imread(os.path.join(_PATH_CURRENT, "imgs", company, part, data[part], "body.png"))

					if len(masks) == 2:
						body = ut.overlap(body,ut.average(*masks))
					elif len(masks) == 1:
						body = ut.overlap(body,masks[0])
					
					if outputImg is None:
						outputImg = body
					else:
						outputImg = ut.overlap(outputImg, body)
						
				path = os.path.join(_PATH_CURRENT, "imgs", company, "roof", data["roof"]+".png")
				outputImg = ut.overlap(outputImg, ut.imread(path))

				data["img"] = "img/" + name.replace('.', '_')
				
				cv2.imwrite(os.path.join(img_path, name.replace('.', '_') + ".png"), outputImg)

				tmp_img = outputImg[0:128,0:128].copy()
				tmp_img[np.all(tmp_img[:,:,:3] == Color("#e7ffff").getBGR(), axis=-1),:] = 0
				cv2.imwrite(os.path.join(_PATH_TEMP, company + '_' + name.replace('.', '_') + ".png"), tmp_img)
				try:
					if("format" in data):
						template = env.get_template(data["format"] + ".dat")
						render = template.render(data)
						with open(os.path.join(dat_path, name.replace('.', '_') + ".dat"), "w", encoding="utf-8") as f:
							f.write(render)
					
					print("\033[2K\033[G", end="")
				except:
					print("\033[2K\033[G", "", name, "No dat template")
	
	subprocess.run(['makeobj', 'pak128', "../vehicle.Gal_"+re.sub("_(.)",lambda x:x.group(1).upper(),company) + ".pak"], cwd=dat_path)