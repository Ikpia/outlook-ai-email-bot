import { msalInstance, loginRequest, initializeMsal } from "./msalConfig";

export const signInWithMicrosoft = async () => {
  try {
    await initializeMsal(); // Ensure MSAL is initialized
    const loginResponse = await msalInstance.loginPopup(loginRequest);
    return loginResponse.account;
  } catch (error) {
    console.error("Login failed", error);
    return null;
  }
};

export const getAccessToken = async () => {
  try {
    await initializeMsal(); // Ensure MSAL is initialized
    const account = msalInstance.getAllAccounts()[0]; // Get the logged-in user
    if (!account) throw new Error("No active account found");

    const tokenResponse = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account,
    });

    return tokenResponse.accessToken;
  } catch (error) {
    console.error("Token acquisition failed", error);
    return null;
  }
};
