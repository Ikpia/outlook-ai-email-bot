import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PublicClientApplication } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: "YOUR_CLIENT_ID",
    authority: "https://login.microsoftonline.com/YOUR_TENANT_ID",
    redirectUri: "http://localhost:3000",
  },
};

const msalInstance = new PublicClientApplication(msalConfig);

export default function EmailManager() {
  const [categories, setCategories] = useState([
    "Support",
    "Billing",
    "General Inquiry",
  ]);
  const [emails, setEmails] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [scheduledResponses, setScheduledResponses] = useState({});
  const [accessToken, setAccessToken] = useState(null);

  useEffect(() => {
    setEmails([
      {
        id: 1,
        sender: "john@example.com",
        subject: "Billing Issue",
        category: "Billing",
      },
      {
        id: 2,
        sender: "jane@example.com",
        subject: "Technical Support",
        category: "Support",
      },
    ]);
  }, []);

  const handleCategoryChange = (id, category) => {
    setEmails((prev) =>
      prev.map((email) => (email.id === id ? { ...email, category } : email))
    );
  };

  const handleScheduleResponse = (category, time) => {
    setScheduledResponses({ ...scheduledResponses, [category]: time });
  };

  const signIn = async () => {
    try {
      const response = await msalInstance.loginPopup({
        scopes: ["https://graph.microsoft.com/.default"],
      });
      setAccessToken(response.accessToken);
    } catch (error) {
      console.error("Error signing in:", error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Email Management Dashboard</h1>
      <Button onClick={signIn}>Sign in with Microsoft</Button>
      {accessToken && <p>Access Token Acquired</p>}

      {/* Email Categorization Table */}
      <Card>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sender</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Category</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {emails.map((email) => (
                <TableRow key={email.id}>
                  <TableCell>{email.sender}</TableCell>
                  <TableCell>{email.subject}</TableCell>
                  <TableCell>
                    <Select
                      onValueChange={(value) =>
                        handleCategoryChange(email.id, value)
                      }
                    >
                      <SelectTrigger>{email.category}</SelectTrigger>
                      <SelectContent>
                        {categories.map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {cat}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Scheduled Responses */}
      <Card>
        <CardContent>
          <h2 className="text-lg font-semibold">Schedule Responses</h2>
          {categories.map((category) => (
            <div key={category} className="flex items-center gap-4 mt-4">
              <span>{category}</span>
              <Input
                type="time"
                value={scheduledResponses[category] || ""}
                onChange={(e) =>
                  handleScheduleResponse(category, e.target.value)
                }
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Button className="w-full">Save Changes</Button>
    </div>
  );
}
