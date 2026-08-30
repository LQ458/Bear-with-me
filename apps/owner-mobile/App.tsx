import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, Button, FlatList, Platform, SafeAreaView, StyleSheet, Text, TextInput, View } from "react-native";
import Constants from "expo-constants";
import * as SecureStore from "expo-secure-store";
import { CallRoom } from "./src/CallRoom";
import { InboxEvent, Item, Message, OwnerApi, registerOwner } from "./src/api";
import { onNotificationOpened, registerForOwnerNotifications } from "./src/notifications";

const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  Constants.expoConfig?.extra?.apiBaseUrl ??
  "http://localhost:8000";

export default function App() {
  const [session, setSession] = useState("");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [inbox, setInbox] = useState<InboxEvent[]>([]);
  const [selected, setSelected] = useState<InboxEvent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const lastMessage = useRef("");
  const [newLabel, setNewLabel] = useState("");
  const [call, setCall] = useState<{ server_url: string; token: string } | null>(null);
  const [tagCodes, setTagCodes] = useState<Record<string, string>>({});
  const [ready, setReady] = useState(false);
  const [notificationStatus, setNotificationStatus] = useState("Notifications are not registered yet.");
  const api = useMemo(() => (session ? new OwnerApi({ baseUrl: API_BASE, sessionToken: session }) : null), [session]);

  useEffect(() => {
    void SecureStore.getItemAsync("owner_session")
      .then((stored) => {
        if (stored) setSession(stored);
      })
      .finally(() => setReady(true));
  }, []);

  async function refresh() {
    if (!api) return;
    const [nextItems, nextInbox] = await Promise.all([api.listItems(), api.inbox()]);
    setItems(nextItems);
    setInbox(nextInbox);
  }

  useEffect(() => {
    if (!api) return;
    void refresh().catch((error: Error) => Alert.alert("Could not load account", error.message));
    void registerForOwnerNotifications()
      .then((pushToken) => {
        if (!pushToken) {
          setNotificationStatus("System notifications are disabled; use the app inbox.");
          return;
        }
        setNotificationStatus("System notifications enabled.");
        return api.registerDevice(pushToken, Platform.OS === "ios" ? "ios" : "android");
      })
      .catch((error: Error) => setNotificationStatus(`Notifications unavailable: ${error.message}`));
    const unsubscribe = onNotificationOpened((data) => {
      void api.inbox().then((latest) => {
        setInbox(latest);
        const event = latest.find((candidate) => candidate.conversation_ref === data.conversation_ref);
        if (event) setSelected(event);
      }).catch(() => undefined);
    });
    const timer = setInterval(() => void refresh().catch(() => undefined), 5000);
    return () => {
      unsubscribe();
      clearInterval(timer);
    };
  }, [api]);

  useEffect(() => {
    if (!api || !selected) return;
    let active = true;
    lastMessage.current = "";
    const load = async () => {
      const next = await api.messages(selected.conversation_ref, lastMessage.current);
      if (active && next.length) {
        lastMessage.current = next.at(-1)?.created_at ?? lastMessage.current;
        setMessages((current) => [...current, ...next]);
      }
    };
    void load().catch(() => undefined);
    const timer = setInterval(() => void load().catch(() => undefined), 2500);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [api, selected]);

  async function signUp() {
    try {
      const result = await registerOwner(API_BASE, email, name);
      await SecureStore.setItemAsync("owner_session", result.token);
      setSession(result.token);
    } catch (error) {
      Alert.alert("Could not create account", (error as Error).message);
    }
  }

  async function addItem() {
    if (!api || !newLabel.trim()) return;
    try {
      await api.createItem(newLabel.trim());
      setNewLabel("");
      await refresh();
    } catch (error) {
      Alert.alert("Could not add item", (error as Error).message);
    }
  }

  async function send() {
    if (!api || !selected || !newMessage.trim()) return;
    try {
      const message = await api.sendMessage(selected.conversation_ref, newMessage.trim());
      lastMessage.current = message.created_at;
      setMessages((current) => [...current, message]);
      setNewMessage("");
    } catch (error) {
      Alert.alert("Could not send message", (error as Error).message);
    }
  }

  async function startCall() {
    if (!api || !selected) return;
    try {
      const token = await api.callToken(selected.conversation_ref);
      setCall({ server_url: token.server_url, token: token.token });
    } catch (error) {
      Alert.alert("Calling is unavailable", (error as Error).message);
    }
  }
  async function provisionTag(itemRef: string) {
    if (!api) return;
    try {
      const tag = await api.provisionTag(itemRef);
      setTagCodes((current) => ({ ...current, [itemRef]: tag.human_code }));
      Alert.alert("Tag ready", `Short code: ${tag.human_code}\nWrite the NFC URL or print the QR label.`);
    } catch (error) {
      Alert.alert("Could not provision tag", (error as Error).message);
    }
  }

  if (!ready) return <SafeAreaView style={styles.safe}><Text style={styles.muted}>Loading owner session…</Text></SafeAreaView>;
  if (call) return <CallRoom serverUrl={call.server_url} token={call.token} onEnd={() => setCall(null)} />;

  if (!session) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.shell}>
          <Text style={styles.eyebrow}>BEAR WITH ME</Text>
          <Text style={styles.title}>Keep your things findable.</Text>
          <Text style={styles.muted}>Register the owner account used for private notifications.</Text>
          <TextInput style={styles.input} placeholder="Your name" value={name} onChangeText={setName} />
          <TextInput style={styles.input} placeholder="Email" keyboardType="email-address" autoCapitalize="none" value={email} onChangeText={setEmail} />
          <Button title="Create owner account" onPress={() => void signUp()} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <FlatList
        contentContainerStyle={styles.shell}
        data={items}
        keyExtractor={(item) => item.item_ref}
        ListHeaderComponent={
          <>
            <Text style={styles.eyebrow}>OWNER APP</Text>
            <Text style={styles.muted}>{notificationStatus}</Text>
            <Text style={styles.title}>Your items</Text>
            <View style={styles.row}>
              <TextInput
                style={[styles.input, styles.flex]}
                placeholder="Blue water bottle"
                value={newLabel}
                onChangeText={setNewLabel}
              />
              <Button title="Add" onPress={() => void addItem()} />
            </View>
            <Text style={styles.section}>Found reports</Text>
            {inbox.map((event) => (
              <View style={styles.card} key={event.found_ref}>
                <Text style={styles.cardTitle}>{event.label}</Text>
                <Text style={styles.muted}>
                  {event.place}{event.note ? ` — ${event.note}` : ""}
                </Text>
                <Button
                  title="Open anonymous chat"
                  onPress={() => {
                    setSelected(event);
                    setMessages([]);
                  }}
                />
              </View>
            ))}
            {selected && (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Chat about {selected.label}</Text>
                {messages.map((message) => (
                  <Text key={message.message_ref} style={styles.message}>
                    {message.sender_role}: {message.body}
                  </Text>
                ))}
                <TextInput
                  style={styles.input}
                  placeholder="Reply anonymously"
                  value={newMessage}
                  onChangeText={setNewMessage}
                />
                <View style={styles.row}>
                  <Button title="Send" onPress={() => void send()} />
                  <Button title="Call" onPress={() => void startCall()} />
                </View>
              </View>
            )}
            <Text style={styles.section}>Inventory</Text>
          </>
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.label}</Text>
            <Text style={styles.muted}>{item.status}</Text>
            {tagCodes[item.item_ref] && (
              <Text style={styles.code}>Short code: {tagCodes[item.item_ref]}</Text>
            )}
            <Button
              title="Provision NFC / QR tag"
              onPress={() => void provisionTag(item.item_ref)}
            />
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#eef3f7" },
  shell: { width: "100%", maxWidth: 720, alignSelf: "center", padding: 22, gap: 12 },
  eyebrow: { color: "#2f5d9e", fontWeight: "700", letterSpacing: 2 },
  title: { fontSize: 31, fontWeight: "800", color: "#15202b" },
  section: { fontSize: 20, fontWeight: "700", color: "#15202b", marginTop: 18 },
  muted: { color: "#5e6b78", lineHeight: 21 },
  input: { backgroundColor: "white", borderColor: "#b8c5d1", borderWidth: 1, borderRadius: 9, padding: 12, marginVertical: 6 },
  flex: { flex: 1 },
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  card: { backgroundColor: "white", borderRadius: 12, padding: 15, marginVertical: 5, gap: 5 },
  cardTitle: { fontSize: 17, fontWeight: "700" },
  message: { backgroundColor: "#f1f5f8", padding: 8, borderRadius: 8 },
  code: { color: "#2f5d9e", fontWeight: "700", letterSpacing: 1.5 },
});
