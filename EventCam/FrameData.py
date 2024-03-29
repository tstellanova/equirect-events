# automatically generated by the FlatBuffers compiler, do not modify

# namespace: EventCam

import flatbuffers

class FrameData(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAsFrameData(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = FrameData()
        x.Init(buf, n + offset)
        return x

    # FrameData
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

# /// vector of events included in this frame
    # FrameData
    def Events(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 16
            from .ChangeEvent import ChangeEvent
            obj = ChangeEvent()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # FrameData
    def EventsLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # FrameData
    def RisingCount(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

    # FrameData
    def FallingCount(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint32Flags, o + self._tab.Pos)
        return 0

def FrameDataStart(builder): builder.StartObject(3)
def FrameDataAddEvents(builder, events): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(events), 0)
def FrameDataStartEventsVector(builder, numElems): return builder.StartVector(16, numElems, 8)
def FrameDataAddRisingCount(builder, risingCount): builder.PrependUint32Slot(1, risingCount, 0)
def FrameDataAddFallingCount(builder, fallingCount): builder.PrependUint32Slot(2, fallingCount, 0)
def FrameDataEnd(builder): return builder.EndObject()
