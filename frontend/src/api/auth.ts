import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_API_URL || 'http://localhost:8000';

const authService = axios.create({
  baseURL: `${API_BASE_URL}/auth`,
  withCredentials: true
});

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface Role {
  id: number;
  name: string;
}

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  roles: Role[];
}

export const loginUser = async (data: LoginData): Promise<User> => {
  const form_data = new URLSearchParams();
  form_data.append('username', data.username);
  form_data.append('password', data.password);
  const response = await authService.post<User>('/login', form_data, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const registerUser = async (data: RegisterData): Promise<User> => {
  const response = await authService.post<User>('/register', data);
  return response.data;
};

export const fetchCurrentUser = async (): Promise<User> => {
  const response = await authService.get<User>('/me');
  return response.data;
};

export const logoutUser = async (): Promise<void> => {
  await authService.post('/logout');
};

export { AxiosError };
