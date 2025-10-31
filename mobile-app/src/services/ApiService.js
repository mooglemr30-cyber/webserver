import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import CONFIG from '../config';

class ApiService {
  constructor() {
    this.baseURL = null;
    this.token = null;
    this.axiosInstance = null;
  }

  async initialize() {
    // Load server URL and token from storage
    const serverUrl = await AsyncStorage.getItem(CONFIG.STORAGE_KEYS.SERVER_URL);
    const token = await AsyncStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);

    this.baseURL = serverUrl || CONFIG.DEFAULT_SERVER_URL;
    this.token = token;

    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: CONFIG.TIMEOUT.DEFAULT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for auth token
    this.axiosInstance.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearAuth();
        }
        return Promise.reject(error);
      }
    );
  }

  async setServerUrl(url) {
    this.baseURL = url;
    await AsyncStorage.setItem(CONFIG.STORAGE_KEYS.SERVER_URL, url);
    await this.initialize();
  }

  async setToken(token) {
    this.token = token;
    await AsyncStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, token);
  }

  async clearAuth() {
    this.token = null;
    await AsyncStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
    await AsyncStorage.removeItem(CONFIG.STORAGE_KEYS.USER_INFO);
  }

  // Health check
  async healthCheck() {
    const response = await this.axiosInstance.get(CONFIG.API.HEALTH);
    return response.data;
  }

  // Get mobile configuration
  async getMobileConfig() {
    const response = await this.axiosInstance.get(CONFIG.API.MOBILE_CONFIG);
    return response.data;
  }

  // Get tunnel status
  async getTunnelStatus() {
    const response = await this.axiosInstance.get(CONFIG.API.TUNNEL_STATUS);
    return response.data;
  }

  // Start tunnel
  async startTunnel() {
    const response = await this.axiosInstance.post(CONFIG.API.TUNNEL_START);
    return response.data;
  }

  // Stop tunnel
  async stopTunnel() {
    const response = await this.axiosInstance.post(CONFIG.API.TUNNEL_STOP);
    return response.data;
  }

  // Authentication
  async login(username, password) {
    const response = await this.axiosInstance.post(CONFIG.API.LOGIN, {
      username,
      password,
    });

    if (response.data.data?.token) {
      await this.setToken(response.data.data.token);
      await AsyncStorage.setItem(
        CONFIG.STORAGE_KEYS.USER_INFO,
        JSON.stringify(response.data.data.user)
      );
    }

    return response.data;
  }

  async register(username, email, password) {
    const response = await this.axiosInstance.post(CONFIG.API.REGISTER, {
      username,
      email,
      password,
    });
    return response.data;
  }

  // Data storage
  async getAllData() {
    const response = await this.axiosInstance.get(CONFIG.API.DATA);
    return response.data;
  }

  async getData(key) {
    const response = await this.axiosInstance.get(`${CONFIG.API.DATA}/${key}`);
    return response.data;
  }

  async storeData(key, value) {
    const response = await this.axiosInstance.post(CONFIG.API.DATA, {
      key,
      value,
    });
    return response.data;
  }

  async deleteData(key) {
    const response = await this.axiosInstance.delete(`${CONFIG.API.DATA}/${key}`);
    return response.data;
  }

  // File management
  async listFiles() {
    const response = await this.axiosInstance.get(`${CONFIG.API.FILES}/list`);
    return response.data;
  }

  async uploadFile(fileUri, fileName) {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      type: 'application/octet-stream',
      name: fileName,
    });

    const response = await this.axiosInstance.post(
      `${CONFIG.API.FILES}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: CONFIG.TIMEOUT.UPLOAD,
      }
    );
    return response.data;
  }

  async downloadFile(fileName) {
    const response = await this.axiosInstance.get(
      `${CONFIG.API.FILES}/download/${fileName}`,
      {
        responseType: 'blob',
        timeout: CONFIG.TIMEOUT.DOWNLOAD,
      }
    );
    return response.data;
  }

  async deleteFile(fileName) {
    const response = await this.axiosInstance.delete(
      `${CONFIG.API.FILES}/delete/${fileName}`
    );
    return response.data;
  }

  async getStorageInfo() {
    const response = await this.axiosInstance.get(`${CONFIG.API.FILES}/storage-info`);
    return response.data;
  }

  // Program execution
  async listPrograms() {
    const response = await this.axiosInstance.get(`${CONFIG.API.PROGRAMS}/list`);
    return response.data;
  }

  async uploadProgram(fileUri, fileName) {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      type: 'application/octet-stream',
      name: fileName,
    });

    const response = await this.axiosInstance.post(
      `${CONFIG.API.PROGRAMS}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: CONFIG.TIMEOUT.UPLOAD,
      }
    );
    return response.data;
  }

  async executeProgram(programId, args = []) {
    const response = await this.axiosInstance.post(
      `${CONFIG.API.PROGRAMS}/execute/${programId}`,
      { args },
      {
        timeout: CONFIG.TIMEOUT.EXECUTE,
      }
    );
    return response.data;
  }

  async deleteProgram(programId) {
    const response = await this.axiosInstance.delete(
      `${CONFIG.API.PROGRAMS}/delete/${programId}`
    );
    return response.data;
  }

  // Command execution
  async executeCommand(command, interactive = false) {
    const response = await this.axiosInstance.post(
      CONFIG.API.EXECUTE,
      {
        command,
        interactive,
      },
      {
        timeout: CONFIG.TIMEOUT.EXECUTE,
      }
    );
    return response.data;
  }
}

// Export singleton instance
const apiService = new ApiService();
export default apiService;

