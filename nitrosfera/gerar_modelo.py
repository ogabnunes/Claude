import sys, cv2, numpy as np, trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
img_path, out = sys.argv[1], sys.argv[2]
im = cv2.imread(img_path)
b,g,r = [im[:,:,i].astype(np.float32) for i in range(3)]
# "redness" map, upsampled & smoothed for clean edges
redness = np.clip((r - g) / 255.0, 0, 1)
U = 4
big = cv2.resize(redness, None, fx=U, fy=U, interpolation=cv2.INTER_CUBIC)
big = cv2.GaussianBlur(big, (0,0), 2.0)
mask = (big > 0.5).astype(np.uint8)*255
C = 399.5; PX = 0.25  # mm per original pixel -> 800px = 200mm
R_DISC, R_RING_O, R_RING_I = 100.0, 359.5*PX, 324.0*PX
def to_mm(pts):
    x = (pts[:,0]/U - C)*PX; y = -(pts[:,1]/U - C)*PX
    return np.c_[x,y]
cs,_ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
face = Point(0,0).buffer(R_RING_I - 0.6, 256)
polys = []
for c in cs:
    if len(c) < 20: continue
    p = Polygon(to_mm(c[:,0,:].astype(float))).buffer(0)
    if p.is_empty: continue
    if p.within(face) or p.intersection(face).area > 0.9*p.area:
        polys.append(p)
gauge = unary_union(polys).intersection(face).simplify(0.05)
print('gauge parts', getattr(gauge,'geoms',[gauge]).__len__() if hasattr(gauge,'geoms') else 1, 'area mm2', round(gauge.area,1))
CUT_Y = -92.0  # flat base: chord ~78 mm
cut = box(-200, CUT_Y, 200, 200)
disc  = Point(0,0).buffer(R_DISC, 512).intersection(cut)
ring  = Point(0,0).buffer(R_RING_O, 512).difference(Point(0,0).buffer(R_RING_I, 512))
white = Point(0,0).buffer(R_RING_I, 512).difference(gauge)
T, INLAY = 30.0, 1.2
def ext(poly, h, z0):
    m = trimesh.creation.extrude_polygon(poly, h) if poly.geom_type=='Polygon' else \
        trimesh.util.concatenate([trimesh.creation.extrude_polygon(p,h) for p in poly.geoms])
    m.apply_translation([0,0,z0]); return m
import zipfile
def write_3mf(path, parts):
    objs=[]; comps=[]
    mats=''.join(f'<base name="{n}" displaycolor="{c}FF"/>' for n,_,c in parts)
    for i,(n,m,c) in enumerate(parts):
        oid=i+2
        v=''.join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{d:.4f}"/>' for a,b,d in m.vertices)
        t=''.join(f'<triangle v1="{a}" v2="{b}" v3="{d}"/>' for a,b,d in m.faces)
        objs.append(f'<object id="{oid}" name="{n}" type="model" pid="1" pindex="{i}"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        comps.append(f'<component objectid="{oid}"/>')
    asm=len(parts)+2
    model=('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
      '<metadata name="Title">Nitrosfera logo</metadata><resources>'
      f'<basematerials id="1">{mats}</basematerials>'+''.join(objs)+
      f'<object id="{asm}" name="nitrosfera_logo" type="model"><components>'+''.join(comps)+'</components></object>'
      f'</resources><build><item objectid="{asm}" transform="1 0 0 0 1 0 0 0 1 110 110 0"/></build></model>')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model', model)
# Colour version: red body (with gauge flush on top), black + white inlays in top 1.2 mm
red_body = trimesh.boolean.union([ext(disc, T-INLAY, 0), ext(gauge, INLAY, T-INLAY),
    ext(disc.difference(Point(0,0).buffer(R_RING_O,512)), INLAY, T-INLAY)], engine='manifold')
black = ext(ring, INLAY, T-INLAY)
whitem = ext(white, INLAY, T-INLAY)
for n,m in [('vermelho',red_body),('preto',black),('branco',whitem)]:
    print(n, 'watertight', m.is_watertight, 'vol cm3', round(m.volume/1000,1), 'bounds', np.round(m.bounds,1).tolist())
    m.export(f'{out}/nitrosfera_cor_{n}.stl')
# Single-colour relief version: 28 mm disc, ring + gauge raised 2 mm
mono = trimesh.boolean.union([ext(disc, 28.0, 0), ext(ring, 2.0, 28.0), ext(gauge, 2.0, 28.0)], engine='manifold')
print('mono watertight', mono.is_watertight, 'vol', round(mono.volume/1000,1)); mono.export(f'{out}/nitrosfera_1cor_relevo.stl')
# 3MF: one object, three parts
write_3mf(f'{out}/nitrosfera_3cores.3mf', [('vermelho',red_body,'#E60000'),('preto',black,'#111111'),('branco',whitem,'#FFFFFF')])
# preview
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
fig,ax = plt.subplots(figsize=(6,6))
def draw(g, col):
    for p in (g.geoms if hasattr(g,'geoms') else [g]):
        ax.add_patch(MP(np.array(p.exterior.coords), fc=col, ec='none'))
        for i in p.interiors: ax.add_patch(MP(np.array(i.coords), fc=bgc, ec='none'))
bgc='#dddddd'
draw(disc,'#e60000'); draw(ring.intersection(disc),'#111'); draw(white,'#fff'); draw(gauge,'#e60000')
ax.axhline(CUT_Y, color='gray', lw=3); ax.set_xlim(-105,105); ax.set_ylim(-105,105); ax.set_aspect('equal'); ax.set_facecolor(bgc)
ax.set_title('Vista frontal (mm) - base plana em y=%.0f' % CUT_Y)
fig.savefig(f'{out}/preview_frente.png', dpi=120, bbox_inches='tight')
