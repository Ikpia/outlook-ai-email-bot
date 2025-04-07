import { AuthenticatedTemplate, UnauthenticatedTemplate, useMsal } from '@azure/msal-react';
//import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { loginRequest } from '../../auth/auth-config';
import { Link } from 'react-router-dom';

function Header() {
  //const { instance } = useMsal();

  const { instance } = useMsal();
  const activeAccount = instance.getActiveAccount();
  //const account = accounts[0];

  const handleLoginRedirect = () => {
    instance
      .loginRedirect({
        ...loginRequest,
        redirectUri: '/',
        prompt: 'create',
      })
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .catch((error: any) => {
        console.error(error);
        throw error;
      });
  };

  const handleLogoutRedirect = () => {
    instance.logoutRedirect({
      postLogoutRedirectUri: '/',
    });
  };


  
  
/*
  const handleLogin = async () => {
    try {
      // 1) interactive login
      await instance.loginPopup(loginRequest);
      // 2) then acquire an access token silently
      const result = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
      });
      console.log("Access Token:", result.accessToken);
      localStorage.setItem("accessToken", result.accessToken);
    } catch (e) {
      if (e instanceof InteractionRequiredAuthError) {
        // fallback to popup if silent fails
        const result = await instance.acquireTokenPopup(loginRequest);
        console.log("Access Token (popup):", result.accessToken);
        localStorage.setItem("accessToken", result.accessToken);
      } else {
        console.error(e);
      }
    }
  };

  /*
  const callGraph = async () => {
    const token = localStorage.getItem("accessToken");
    if (!token) return alert("Please login first");
    try {
      const res = await axios.get("https://graph.microsoft.com/v1.0/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log("Graph /me:", res.data);
    } catch (err) {
      console.error(err);
    }
  };
  const handleLogin = () => {
    instance
      .loginPopup({
        scopes: [
          "openid",
          "profile",
          "email",
          "https://graph.microsoft.com/Mail.Read",
          "https://graph.microsoft.com/Mail.ReadWrite",
          "https://graph.microsoft.com/Mail.Send",
        ],
      })
      .then((response) => {
        console.log("Access Token:", response.accessToken);
        // Store the access token securely
        localStorage.setItem("accessToken", response.accessToken);
        // Proceed with using the access token for API calls
      })
      .catch((error) => {
        console.error("Login failed:", error);
      });
  };
*/


  return (
    <div className="w-screen max-w-full navbar bg-primary text-primary-content ">
      <div className="navbar-start">
        <div className="dropdown">
          <label tabIndex={0} className="btn btn-ghost lg:hidden">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h8m-8 6h16" />
            </svg>
          </label>
          <ul tabIndex={0} className="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
            <li><Link to="/">Home</Link></li>
            <li><Link className="btn btn-primary" to="/schedule-response">Schedule-response</Link></li>
            <li><Link to="/email">Emails</Link></li>
          </ul>
        </div>
        <Link to="/" className="btn btn-ghost normal-case text-xl">Email Management System</Link>
      </div>
      <div className="navbar-center hidden lg:flex">
        <ul className="menu menu-horizontal px-1">
          <li><Link className="btn btn-primary" to="/">Home</Link></li>
          <li><Link className="btn btn-primary" to="/schedule-response">Schedule-response</Link></li>
          <li><Link className="btn btn-primary" to="/email">Emails</Link></li>

        </ul>
      </div>
      <div className="navbar-end">
        <AuthenticatedTemplate>
          {activeAccount && (
            <>
              <span className="mr-4">Welcome, {activeAccount.name}</span>
              <button className="btn btn-ghost btn-sm" onClick={handleLogoutRedirect}>Logout</button>
            </>
          )}
        </AuthenticatedTemplate>
        <UnauthenticatedTemplate>
          <button className="btn btn-ghost btn-sm" onClick={handleLoginRedirect}>Login</button>
        </UnauthenticatedTemplate>
      </div>
    </div>
  );
}

export default Header;