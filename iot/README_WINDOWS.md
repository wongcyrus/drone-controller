# Windows IoT Client for Drone Controller

This directory contains Windows-optimized versions of the IoT client for connecting the drone controller to AWS IoT Core.

## Windows-Specific Features

### 1. Enhanced Compatibility
- **Windows Path Handling**: Proper handling of Windows file paths and directory separators
- **UTF-8 Encoding**: Explicit UTF-8 encoding for all file operations
- **Platform Detection**: Automatic detection and optimization for Windows platform
- **Signal Handling**: Windows-compatible signal handling for graceful shutdown

### 2. Improved Stability
- **Extended Timeouts**: Longer connection timeouts optimized for Windows networking
- **Retry Logic**: Enhanced retry mechanism with exponential backoff
- **WebSocket Fallback**: Automatic fallback to WebSocket connection if mTLS fails
- **Error Recovery**: Better error handling and recovery mechanisms

### 3. Windows Service Support
- **Service Installation**: Run as a Windows service for background operation
- **Service Management**: PowerShell scripts for service lifecycle management
- **Logging**: Comprehensive logging with Windows-specific log formatting
- **Auto-restart**: Service configured to restart automatically on failure

## Files Overview

### Core Files
- `pubsub_windows.py` - Windows-optimized IoT MQTT client
- `settings_windows.yaml` - Windows-specific configuration file
- `action_executor.py` - Modified with Windows-specific timeouts and handling

### Launcher Scripts
- `run_iot_client.ps1` - PowerShell script for running the IoT client
- `run_iot_client.bat` - Batch file for easy Windows execution
- `Manage-IoTService.ps1` - PowerShell script for Windows service management

### Configuration
- `requirements.txt` - Python dependencies
- `settings.yaml` - Default configuration (fallback)
- `certifications/` - Directory for AWS IoT certificates

## Quick Start

### Method 1: Using Batch File (Easiest)
1. Double-click `run_iot_client.bat`
2. The script will automatically:
   - Check Python installation
   - Create virtual environment
   - Install dependencies
   - Start the IoT client

### Method 2: Using PowerShell
1. Open PowerShell in the IoT directory
2. Run: `.\run_iot_client.ps1`
3. Optional parameters:
   ```powershell
   .\run_iot_client.ps1 -ConfigFile "settings_windows.yaml" -Verbose
   ```

### Method 3: Direct Python Execution
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the client
python pubsub_windows.py --config settings_windows.yaml --verbose
```

## Windows Service Installation

### Install as Service
```powershell
# Run PowerShell as Administrator
.\Manage-IoTService.ps1 install
```

### Service Management Commands
```powershell
# Start the service
.\Manage-IoTService.ps1 start

# Stop the service
.\Manage-IoTService.ps1 stop

# Restart the service
.\Manage-IoTService.ps1 restart

# Check service status
.\Manage-IoTService.ps1 status

# View service logs
.\Manage-IoTService.ps1 logs

# Uninstall the service
.\Manage-IoTService.ps1 uninstall
```

## Configuration

### Windows-Specific Settings
The `settings_windows.yaml` file contains Windows-optimized settings:

```yaml
# Windows-specific configuration
windows:
  connection_timeout: 15        # Extended timeout for Windows
  max_retry_attempts: 5         # More retry attempts
  websocket_fallback: true      # Enable WebSocket fallback
  log_level: "INFO"            # Logging level
  file_logging: true           # Enable file logging
  log_file: "logs\\iot_client.log"  # Windows log path
  request_timeout: 2.0         # Local request timeout
  sleep_interval: 0.2          # Action monitoring interval
```

### Certificate Setup
1. Place AWS IoT certificates in the `certifications/drone_1/` directory:
   - `drone_1.cert.pem` - Device certificate
   - `drone_1.private.key` - Private key
   - `AmazonRootCA1.pem` - Root CA certificate

2. Update `settings_windows.yaml` with your AWS IoT endpoint and thing name

### Environment Variables
Set these environment variables for AWS credentials (optional):
```powershell
$env:IoTRobotAccessKeyId = "your-access-key"
$env:IoTRobotSecretAccessKey = "your-secret-key"
```

## Logging

### Log Files Location
- Service logs: `logs/service.log`
- IoT client logs: `logs/iot_client_YYYY-MM-DD.log`
- Service management logs: `logs/service_management.log`

### Log Levels
- `DEBUG` - Detailed debugging information
- `INFO` - General information messages
- `WARNING` - Warning messages
- `ERROR` - Error messages

## Troubleshooting

### Common Issues

#### 1. Python Not Found
- Install Python from python.org
- Ensure Python is added to PATH during installation
- Restart command prompt/PowerShell after installation

#### 2. Certificate Errors
- Verify certificate files exist in the correct directory
- Check file permissions (ensure readable by the application)
- Validate certificate format and content

#### 3. Connection Issues
- Check internet connectivity
- Verify AWS IoT endpoint configuration
- Test with WebSocket fallback enabled
- Check Windows firewall settings

#### 4. Service Installation Fails
- Run PowerShell as Administrator
- Check Windows Event Viewer for detailed error messages
- Verify Python path is correct in service configuration

### Debug Mode
Run with verbose logging to troubleshoot issues:
```powershell
python pubsub_windows.py --config settings_windows.yaml --verbose --log-file debug.log
```

### Network Connectivity Test
Test AWS IoT connectivity:
```powershell
# Test MQTT over TLS (port 8883)
Test-NetConnection a1qlex7vqi1791-ats.iot.us-east-1.amazonaws.com -Port 8883

# Test WebSocket (port 443)
Test-NetConnection a1qlex7vqi1791-ats.iot.us-east-1.amazonaws.com -Port 443
```

## Performance Considerations

### Windows Optimizations
- **Connection Pooling**: Reuses connections where possible
- **Threading**: Optimized threading for Windows
- **Memory Management**: Proper cleanup of resources
- **Sleep Intervals**: Adjusted for Windows scheduling

### System Requirements
- Windows 10 or Windows Server 2016+
- Python 3.7 or later
- 256MB RAM minimum
- Internet connectivity
- Administrator privileges (for service installation)

## Security Notes

### Certificate Security
- Store certificates in a secure location
- Use proper file permissions (readable only by service account)
- Rotate certificates regularly as per AWS IoT best practices

### Service Security
- Run service with minimal required privileges
- Consider using a dedicated service account
- Monitor service logs for security events

## Integration with Drone Controller

The Windows IoT client integrates with the main drone controller system:

1. **MQTT Communication**: Receives action commands via AWS IoT Core
2. **Action Execution**: Forwards commands to the local robot controller
3. **Status Reporting**: Reports action status back through MQTT
4. **Error Handling**: Manages errors and retries automatically

## Support

For issues specific to the Windows version:

1. Check the logs in the `logs/` directory
2. Run with `--verbose` flag for detailed output
3. Verify certificate and configuration files
4. Test network connectivity to AWS IoT
5. Review Windows Event Viewer for service-related issues

## Version History

- **v1.0** - Initial Windows-optimized version
  - Windows path handling
  - Enhanced error recovery
  - PowerShell management scripts
  - Windows service support
