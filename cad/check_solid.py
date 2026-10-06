"""STEP がソリッドとして成立しているかを検査する（開いた縁・非多様体辺・極小の辺/面）。
使い方: python check_solid.py 980-4603-000.step"""
import sys
from collections import Counter
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp

def check(path):
    s = cq.importers.importStep(path)
    sh = s.val()
    m = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(sh.wrapped, TopAbs_EDGE, TopAbs_FACE, m)
    cnt = Counter(m.FindFromIndex(i).Size() for i in range(1, m.Extent() + 1))
    shells = s.shells().vals()
    res = dict(type=sh.ShapeType(), valid=BRepCheck_Analyzer(sh.wrapped).IsValid(), solids=s.solids().size(),
               shells=len(shells), closed=all(x.Closed() for x in shells), faces=len(s.faces().vals()),
               free_edges=cnt.get(1, 0), nonmanifold_edges=sum(v for k, v in cnt.items() if k > 2),
               tiny_edges=sum(1 for e in s.edges().vals() if e.Length() < 0.05),
               tiny_faces=sum(1 for f in s.faces().vals() if f.Area() < 0.05), volume=round(sh.Volume()))
    return res

if __name__ == "__main__":
    for k, v in check(sys.argv[1] if len(sys.argv) > 1 else "980-4603-000.step").items():
        print(f"{k:18s}{v}")
