import axios from "axios";
/*
const getAccessToken = async () => {
  try {
    const fetch_email_response = await axios.get("http://localhost:5000/fetch-outlook-emails");
    if (fetch_email_response.status === 200) {
      const response = await axios.get("http://localhost:5000/get-emails")
    }
    console.log(auth_url);
    ;
    console.log(response.data["access_token"]);
  } catch (error) {
    console.log(error);
  }
};
*/

const api = axios.create({
  baseURL: "http://localhost:5000",
});

// Add a request interceptor to include the token in requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers.Authorization = `Bearer ${process.env.REACT_APP_API_TOKEN}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
