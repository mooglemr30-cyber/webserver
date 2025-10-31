import React, {useEffect, useState} from 'react';
import {
  SafeAreaView,
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import apiService from './services/ApiService';

function App() {
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [serverUrl, setServerUrl] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Tunnel state
  const [useTunnel, setUseTunnel] = useState(false);
  const [tunnelRunning, setTunnelRunning] = useState(false);
  const [tunnelUrl, setTunnelUrl] = useState('');
  const [tunnelLoading, setTunnelLoading] = useState(false);

  // Auth state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Data storage state
  const [dataKey, setDataKey] = useState('');
  const [dataValue, setDataValue] = useState('');
  const [storedData, setStoredData] = useState({});

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      await apiService.initialize();

      // Check if server is accessible
      const health = await apiService.healthCheck();
      if (health.success) {
        setConnected(true);
        setServerUrl(apiService.baseURL);

        // Check tunnel status
        try {
          const tunnelStatus = await apiService.getTunnelStatus();
          if (tunnelStatus.success && tunnelStatus.data) {
            setTunnelRunning(tunnelStatus.data.running || false);
            if (tunnelStatus.data.url) {
              setTunnelUrl(tunnelStatus.data.url);
            }
          }
        } catch (tunnelError) {
          console.log('Tunnel status check failed:', tunnelError);
        }
      }
    } catch (error) {
      console.error('Initialization error:', error);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      setLoading(true);
      const response = await apiService.login(username, password);

      if (response.success) {
        setIsAuthenticated(true);
        Alert.alert('Success', 'Logged in successfully!');
        loadStoredData();
      } else {
        Alert.alert('Error', response.error || 'Login failed');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSetServerUrl = async () => {
    try {
      setLoading(true);
      await apiService.setServerUrl(serverUrl);
      await initializeApp();
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const loadStoredData = async () => {
    try {
      const response = await apiService.getAllData();
      if (response.success) {
        setStoredData(response.data || {});
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleStoreData = async () => {
    if (!dataKey || !dataValue) {
      Alert.alert('Error', 'Please enter both key and value');
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.storeData(dataKey, dataValue);

      if (response.success) {
        Alert.alert('Success', 'Data stored successfully!');
        setDataKey('');
        setDataValue('');
        loadStoredData();
      } else {
        Alert.alert('Error', response.error || 'Failed to store data');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to store data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteData = async (key) => {
    try {
      const response = await apiService.deleteData(key);
      if (response.success) {
        Alert.alert('Success', 'Data deleted successfully!');
        loadStoredData();
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to delete data');
    }
  };

  const handleStartTunnel = async () => {
    try {
      setTunnelLoading(true);
      const response = await apiService.startTunnel();

      if (response.success) {
        setTunnelRunning(true);
        if (response.data && response.data.url) {
          setTunnelUrl(response.data.url);
        }
        Alert.alert('Success', 'Tunnel started successfully!');
      } else {
        Alert.alert('Error', response.error || 'Failed to start tunnel');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to start tunnel');
    } finally {
      setTunnelLoading(false);
    }
  };

  const handleStopTunnel = async () => {
    try {
      setTunnelLoading(true);
      const response = await apiService.stopTunnel();

      if (response.success) {
        setTunnelRunning(false);
        setTunnelUrl('');
        Alert.alert('Success', 'Tunnel stopped successfully!');
      } else {
        Alert.alert('Error', response.error || 'Failed to stop tunnel');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to stop tunnel');
    } finally {
      setTunnelLoading(false);
    }
  };

  const handleRefreshTunnelStatus = async () => {
    try {
      const tunnelStatus = await apiService.getTunnelStatus();
      if (tunnelStatus.success && tunnelStatus.data) {
        setTunnelRunning(tunnelStatus.data.running || false);
        if (tunnelStatus.data.url) {
          setTunnelUrl(tunnelStatus.data.url);
        }
      }
    } catch (error) {
      console.log('Failed to refresh tunnel status:', error);
    }
  };

  if (loading && !connected) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Connecting to server...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!connected) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView style={styles.scrollView}>
          <View style={styles.content}>
            <Text style={styles.title}>🚀 Webserver Mobile</Text>
            <Text style={styles.subtitle}>Connect to your server</Text>

            <View style={styles.card}>
              <Text style={styles.label}>Server URL:</Text>
              <TextInput
                style={styles.input}
                placeholder="https://xxxxx.trycloudflare.com"
                value={serverUrl}
                onChangeText={setServerUrl}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                style={styles.button}
                onPress={handleSetServerUrl}
                disabled={loading}>
                <Text style={styles.buttonText}>
                  {loading ? 'Connecting...' : 'Connect'}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>📱 Setup Instructions:</Text>
              <Text style={styles.infoText}>
                1. Start your server on Ubuntu{'\n'}
                2. Copy the tunnel URL from server logs{'\n'}
                3. Paste it above and click Connect{'\n'}
                4. Login with your credentials
              </Text>
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView style={styles.scrollView}>
          <View style={styles.content}>
            <Text style={styles.title}>🔐 Login</Text>
            <Text style={styles.subtitle}>Connected: {serverUrl}</Text>

            <View style={styles.card}>
              <Text style={styles.label}>Username:</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter username"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
              />

              <Text style={styles.label}>Password:</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />

              <TouchableOpacity
                style={styles.button}
                onPress={handleLogin}
                disabled={loading}>
                <Text style={styles.buttonText}>
                  {loading ? 'Logging in...' : 'Login'}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.infoCard}>
              <Text style={styles.infoText}>
                Default credentials:{'\n'}
                Username: admin{'\n'}
                Password: admin123
              </Text>
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.content}>
          <Text style={styles.title}>✅ Connected</Text>
          <Text style={styles.subtitle}>{serverUrl}</Text>

          {/* Tunnel Control Section */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>🔒 Secure Tunnel</Text>

            <View style={styles.tunnelStatus}>
              <View style={styles.statusIndicator}>
                <View style={[
                  styles.statusDot,
                  tunnelRunning ? styles.statusDotActive : styles.statusDotInactive
                ]} />
                <Text style={styles.statusText}>
                  Tunnel: {tunnelRunning ? 'Running' : 'Stopped'}
                </Text>
              </View>
              <TouchableOpacity
                style={styles.refreshButton}
                onPress={handleRefreshTunnelStatus}>
                <Text style={styles.refreshButtonText}>🔄</Text>
              </TouchableOpacity>
            </View>

            {tunnelRunning && tunnelUrl && (
              <View style={styles.tunnelUrlBox}>
                <Text style={styles.tunnelUrlLabel}>Tunnel URL:</Text>
                <Text style={styles.tunnelUrlText}>{tunnelUrl}</Text>
              </View>
            )}

            <View style={styles.tunnelButtons}>
              <TouchableOpacity
                style={[styles.tunnelButton, tunnelRunning && styles.tunnelButtonDisabled]}
                onPress={handleStartTunnel}
                disabled={tunnelLoading || tunnelRunning}>
                <Text style={styles.tunnelButtonText}>
                  {tunnelLoading && !tunnelRunning ? 'Starting...' : '▶ Start Tunnel'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.tunnelButton, styles.tunnelButtonStop, !tunnelRunning && styles.tunnelButtonDisabled]}
                onPress={handleStopTunnel}
                disabled={tunnelLoading || !tunnelRunning}>
                <Text style={styles.tunnelButtonText}>
                  {tunnelLoading && tunnelRunning ? 'Stopping...' : '⏹ Stop Tunnel'}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.infoBox}>
              <Text style={styles.infoBoxText}>
                💡 By default, the app uses local connection. Start the tunnel only when accessing remotely.
              </Text>
            </View>
          </View>

          {/* Store Data Section */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>📝 Store Data</Text>

            <Text style={styles.label}>Key:</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter key"
              value={dataKey}
              onChangeText={setDataKey}
            />

            <Text style={styles.label}>Value:</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter value"
              value={dataValue}
              onChangeText={setDataValue}
              multiline
            />

            <TouchableOpacity
              style={styles.button}
              onPress={handleStoreData}
              disabled={loading}>
              <Text style={styles.buttonText}>
                {loading ? 'Storing...' : 'Store Data'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Stored Data Section */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>💾 Stored Data</Text>
            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={loadStoredData}>
              <Text style={styles.secondaryButtonText}>Refresh</Text>
            </TouchableOpacity>

            {Object.keys(storedData).length === 0 ? (
              <Text style={styles.emptyText}>No data stored yet</Text>
            ) : (
              Object.entries(storedData).map(([key, value]) => (
                <View key={key} style={styles.dataItem}>
                  <View style={styles.dataContent}>
                    <Text style={styles.dataKey}>{key}</Text>
                    <Text style={styles.dataValue}>
                      {JSON.stringify(value)}
                    </Text>
                  </View>
                  <TouchableOpacity
                    onPress={() => handleDeleteData(key)}
                    style={styles.deleteButton}>
                    <Text style={styles.deleteButtonText}>Delete</Text>
                  </TouchableOpacity>
                </View>
              ))
            )}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 8,
  },
  input: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
    marginBottom: 12,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
    padding: 16,
  },
  dataItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    marginBottom: 8,
  },
  dataContent: {
    flex: 1,
    marginRight: 12,
  },
  dataKey: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  dataValue: {
    fontSize: 12,
    color: '#666',
  },
  deleteButton: {
    backgroundColor: '#FF3B30',
    borderRadius: 6,
    padding: 8,
    paddingHorizontal: 12,
  },
  deleteButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  tunnelStatus: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusDotActive: {
    backgroundColor: '#34C759',
  },
  statusDotInactive: {
    backgroundColor: '#FF3B30',
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  refreshButton: {
    padding: 8,
  },
  refreshButtonText: {
    fontSize: 20,
  },
  tunnelUrlBox: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  tunnelUrlLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  tunnelUrlText: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
  tunnelButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 12,
  },
  tunnelButton: {
    flex: 1,
    backgroundColor: '#34C759',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  tunnelButtonStop: {
    backgroundColor: '#FF3B30',
  },
  tunnelButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  tunnelButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  infoBox: {
    backgroundColor: '#FFF3CD',
    borderRadius: 8,
    padding: 12,
  },
  infoBoxText: {
    fontSize: 12,
    color: '#856404',
    lineHeight: 18,
  },
});

export default App;

