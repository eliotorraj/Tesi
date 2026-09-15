// Read-only AMD ADL interface. ABI: AMD Display Library headers and documentation.
// No clock, voltage, fan, power-limit, driver or operating-system settings are changed.
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public sealed class AmdSensors : IDisposable {
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr Allocate(int count);
    private static readonly Allocate Allocator = Marshal.AllocHGlobal;
    private IntPtr context = IntPtr.Zero;
    private readonly List<int> indices = new List<int>();
    private readonly List<string> names = new List<string>();
    private const string Dll = @"C:\Windows\System32\atiadlxx.dll";
    [DllImport(Dll, CallingConvention=CallingConvention.Cdecl)]
    private static extern int ADL2_Main_Control_Create(Allocate allocator,int connected,ref IntPtr context);
    [DllImport(Dll, CallingConvention=CallingConvention.Cdecl)]
    private static extern int ADL2_Main_Control_Destroy(IntPtr context);
    [DllImport(Dll, CallingConvention=CallingConvention.Cdecl)]
    private static extern int ADL2_Adapter_NumberOfAdapters_Get(IntPtr context,ref int count);
    [DllImport(Dll, CallingConvention=CallingConvention.Cdecl)]
    private static extern int ADL2_Adapter_AdapterInfo_Get(IntPtr context,IntPtr buffer,int bytes);
    [DllImport(Dll, CallingConvention=CallingConvention.Cdecl)]
    private static extern int ADL2_New_QueryPMLogData_Get(IntPtr context,int index,IntPtr data);
    public sealed class Sample {
        public int adapter_index;
        public string adapter_name;
        public int return_code;
        public int? edge_c, hotspot_c, memory_c, fan_rpm, asic_power_w, gpu_activity_percent;
    }
    public AmdSensors() {
        int code=ADL2_Main_Control_Create(Allocator,1,ref context);
        if(code!=0) throw new Exception("ADL initialization: "+code);
        int count=0;
        if(ADL2_Adapter_NumberOfAdapters_Get(context,ref count)!=0 || count<1 || count>250)
            throw new Exception("ADL adapter enumeration failed");
        const int stride=1572;
        IntPtr buffer=Marshal.AllocHGlobal(count*stride);
        try {
            for(int i=0;i<count*stride;i+=4) Marshal.WriteInt32(buffer,i,0);
            for(int i=0;i<count;i++) Marshal.WriteInt32(buffer,i*stride,stride);
            if(ADL2_Adapter_AdapterInfo_Get(context,buffer,count*stride)!=0) throw new Exception("ADL adapter data failed");
            var physical = new HashSet<string>();
            for(int i=0;i<count;i++) {
                string key = Marshal.ReadInt32(buffer,i*stride+264)+":"+Marshal.ReadInt32(buffer,i*stride+268)+":"+Marshal.ReadInt32(buffer,i*stride+272);
                if(!physical.Add(key)) continue;
                int index=Marshal.ReadInt32(buffer,i*stride+4);
                if(indices.Contains(index)) continue;
                indices.Add(index);
                names.Add(Marshal.PtrToStringAnsi(IntPtr.Add(buffer,i*stride+280)));
            }
        } finally {Marshal.FreeHGlobal(buffer);}
    }
    private static int? Sensor(IntPtr data,int index) {
        return Marshal.ReadInt32(data,4+8*index)!=0 ? (int?)Marshal.ReadInt32(data,8+8*index) : null;
    }
    public Sample[] Read() {
        var result=new List<Sample>();
        IntPtr data=Marshal.AllocHGlobal(2052);
        try {
            for(int i=0;i<indices.Count;i++) {
                for(int j=0;j<2052;j+=4) Marshal.WriteInt32(data,j,0);
                Marshal.WriteInt32(data,0,2052);
                int code=ADL2_New_QueryPMLogData_Get(context,indices[i],data);
                var row=new Sample {adapter_index=indices[i],adapter_name=names[i],return_code=code};
                if(code==0) {
                    row.edge_c=Sensor(data,8); row.hotspot_c=Sensor(data,27);
                    row.memory_c=Sensor(data,9); row.fan_rpm=Sensor(data,14);
                    row.asic_power_w=Sensor(data,23); row.gpu_activity_percent=Sensor(data,19);
                }
                result.Add(row);
            }
        } finally {Marshal.FreeHGlobal(data);}
        return result.ToArray();
    }
    public void Dispose() {if(context!=IntPtr.Zero){ADL2_Main_Control_Destroy(context);context=IntPtr.Zero;}}
}
