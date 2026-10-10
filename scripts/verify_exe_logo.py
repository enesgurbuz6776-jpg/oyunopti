"""Fail the release build if the Windows EXE does not contain the real OyunOpti ICO.

PyInstaller printing "Copying icon to EXE" isn't sufficient: inspect PE icon
resources and byte-compare them with the icon rendered from the site's icon.svg.
"""
import struct
import sys
from pathlib import Path
import pefile

def icon_images(ico_path):
    data=Path(ico_path).read_bytes()
    if len(data)<6: raise AssertionError("Empty ICO")
    reserved, type_, count=struct.unpack_from("<HHH",data,0)
    assert (reserved,type_) == (0,1) and count>=3, "Invalid ICO directory"
    images=set()
    dimensions=set()
    for index in range(count):
        w,h,ncolors,rsv,planes,bits,size,offset=struct.unpack_from("<BBBBHHII",data,6+16*index)
        width,height=w or 256,h or 256
        image=data[offset:offset+size]
        assert len(image)==size and size>100, f"Bad ICO image at {index}"
        images.add(image)
        dimensions.add((width,height))
    assert (256,256) in dimensions and (32,32) in dimensions, "Missing logo icon sizes"
    return images

def resource_icons(exe_path):
    pe=pefile.PE(str(exe_path),fast_load=False)
    try:
        assert hasattr(pe,"DIRECTORY_ENTRY_RESOURCE"),"EXE has no resources"
        images=[]
        group_count=0
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id==14:
                group_count+=len(entry.directory.entries)
            if entry.id!=3:
                continue
            for icon_entry in entry.directory.entries:
                for lang in icon_entry.directory.entries:
                    data=lang.data.struct
                    images.append(pe.get_data(data.OffsetToData,data.Size))
        assert group_count>0,"Missing RT_GROUP_ICON Windows Explorer desktop icon"
        assert images, "Missing RT_ICON resource"
        return images
    finally:
        pe.close()

def main():
    ico=Path("desktop/assets/oyunopti.ico")
    exe=Path(sys.argv[1] if len(sys.argv)>1 else "dist/OyunOpti-FPS-Booster-v0.5.2.exe")
    source=icon_images(ico)
    embedded=resource_icons(exe)
    unmatched=[a for a in embedded if a not in source]
    assert not unmatched, ("The EXE has unexpected/default Python icons! "
                           f"{len(unmatched)} of {len(embedded)} resources are wrong")
    assert len(embedded)>=3,"Too few embedded icon resolutions"
    print(f"PASS: {len(embedded)} authentic OyunOpti logo resources inside {exe.name}")
if __name__=="__main__":
    main()
