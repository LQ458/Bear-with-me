export type Item = {
  item_ref: string;
  owner_ref: string;
  label: string;
  private_description: string;
  status: "active" | "lost" | "recovered";
  created_at: string;
};

export type InboxEvent = {
  found_ref: string;
  conversation_ref: string;
  item_ref: string;
  label: string;
  place: string;
  note: string;
  conversation_status: "open" | "closed";
  created_at: string;
};

export type Message = {
  message_ref: string;
  conversation_ref: string;
  sender_role: "owner" | "finder" | "authority";
  body: string;
  created_at: string;
};

export type TagProvisioning = { tag_ref: string; item_ref: string; secret: string; human_code: string; finder_url: string };
export type RecordingBootstrap = {
  session_token: string;
  items: Array<{ item_ref: string; label: string; finder_url: string }>;
  item_ref: string;
  label: string;
  finder_url: string;
};

type Config = { baseUrl: string; sessionToken: string };

export class OwnerApi {
  constructor(private readonly config: Config) {}

  async listItems(): Promise<Item[]> {
    const response = await this.request<{ items: Item[] }>("/items");
    return response.items;
  }

  async createItem(label: string, description = ""): Promise<Item> {
    return this.request<Item>("/items", {
      method: "POST",
      body: JSON.stringify({ label, description }),
    });
  }

  async provisionTag(itemRef: string): Promise<TagProvisioning> {
    return this.request<TagProvisioning>(`/items/${encodeURIComponent(itemRef)}/tags`, {
      method: "POST",
    });
  }

  async inbox(): Promise<InboxEvent[]> {
    const response = await this.request<{ events: InboxEvent[] }>("/owner/inbox");
    return response.events;
  }

  async messages(conversationRef: string, after = ""): Promise<Message[]> {
    const response = await this.request<{ messages: Message[] }>(
      `/owner/conversations/${encodeURIComponent(conversationRef)}/messages?after=${encodeURIComponent(after)}`,
    );
    return response.messages;
  }

  async sendMessage(conversationRef: string, body: string): Promise<Message> {
    return this.request<Message>(`/owner/conversations/${encodeURIComponent(conversationRef)}/messages`, {
      method: "POST",
      body: JSON.stringify({ body }),
    });
  }

  async registerDevice(token: string, platform: "ios" | "android" | "web"): Promise<void> {
    await this.request("/owner/devices", {
      method: "POST",
      body: JSON.stringify({ token, platform }),
    });
  }


  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.config.baseUrl.replace(/\/$/, "")}/api${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.config.sessionToken}`,
        ...(init.headers ?? {}),
      },
    });
    const body = (await response.json().catch(() => ({}))) as { error?: string } & T;
    if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
    return body;
  }
}

export async function registerOwner(baseUrl: string, email: string, name: string): Promise<{ token: string }> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/auth/register`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ email, name }),
  });
  const body = (await response.json().catch(() => ({}))) as { session_token?: string; error?: string };
  if (!response.ok || !body.session_token) throw new Error(body.error || "Registration failed");
  return { token: body.session_token };
}
export async function requestMagicLink(baseUrl: string, email: string): Promise<{ token: string }> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/auth/magic-link/request`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const body = (await response.json().catch(() => ({}))) as { token?: string; error?: string };
  if (!response.ok || !body.token) throw new Error(body.error || "Could not send magic link");
  return { token: body.token };
}

export async function consumeMagicLink(baseUrl: string, token: string): Promise<{ token: string }> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/auth/magic-link/consume`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const body = (await response.json().catch(() => ({}))) as { session_token?: string; error?: string };
  if (!response.ok || !body.session_token) throw new Error(body.error || "Could not sign in");
  return { token: body.session_token };
}

export async function bootstrapRecording(baseUrl: string): Promise<RecordingBootstrap> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/recording/bootstrap`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
  });
  const body = (await response.json().catch(() => ({}))) as RecordingBootstrap & { error?: string };
  if (!response.ok || !body.session_token || !body.finder_url) {
    throw new Error(body.error || "Could not open the owner workspace");
  }
  return body;
}
