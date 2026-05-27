# FastDDS IDL Example

This directory contains example IDL (Interface Definition Language) files for FastDDS.

## What is IDL?

IDL is used to define the data types that will be exchanged over DDS. The `fastddsgen` tool generates C++ and Python code from IDL files.

## Example: Hello World

```idl
// HelloWorld.idl
module MyModule {
    struct HelloWorld {
        string message;
        long count;
    };
};
```

Generate code:
```bash
fastddsgen -example HelloWorld.idl
```

## Example: Sensor Data

```idl
// SensorData.idl
module Sensors {
    struct TemperatureReading {
        string sensor_id;
        double temperature;
        double humidity;
        long long timestamp;
    };
    
    struct ImuData {
        float accelerometer_x;
        float accelerometer_y;
        float accelerometer_z;
        float gyroscope_x;
        float gyroscope_y;
        float gyroscope_z;
        long long timestamp;
    };
};
```

## Example: Vehicle State (for CyberRT/ROS2 bridge)

```idl
// VehicleState.idl
module AutonomousDriving {
    enum DrivingMode {
        MANUAL,
        AUTOPILOT,
        SAFE_STOP
    };
    
    struct Pose3D {
        double x;
        double y;
        double z;
        double roll;
        double pitch;
        double yaw;
    };
    
    struct VehicleState {
        string vehicle_id;
        DrivingMode mode;
        Pose3D pose;
        double velocity;
        double steering_angle;
        long long timestamp;
    };
};
```

## Usage in Docker Container

```bash
# Copy IDL file to container
docker cp MyType.idl <container_id>:/workspace/

# Generate code inside container
docker exec -it <container_id> bash
cd /workspace
fastddsgen -example MyType.idl

# Build the generated example
cd build
cmake ..
make
```

## Common IDL Types

| IDL Type | C++ Type | Python Type |
|----------|----------|-------------|
| `boolean` | `bool` | `bool` |
| `octet` | `uint8_t` | `int` |
| `char` | `char` | `str` |
| `wchar` | `wchar_t` | `str` |
| `short` | `int16_t` | `int` |
| `long` | `int32_t` | `int` |
| `long long` | `int64_t` | `int` |
| `unsigned short` | `uint16_t` | `int` |
| `unsigned long` | `uint32_t` | `int` |
| `float` | `float` | `float` |
| `double` | `double` | `float` |
| `string` | `std::string` | `str` |
| `sequence<T>` | `std::vector<T>` | `list` |

## Resources

- [FastDDS IDL Documentation](https://fast-dds.docs.eprosima.com/en/latest/fastddsgen/idl.html)
- [OMG IDL Specification](https://www.omg.org/spec/IDL)
