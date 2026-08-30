import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, FlatList, Platform, Pressable, SafeAreaView, Share, StyleSheet, Text, TextInput, View } from "react-native";
import Constants from "expo-constants";
import * as SecureStore from "expo-secure-store";
import { InboxEvent, Item, Message, OwnerApi, bootstrapRecording, consumeMagicLink, registerOwner, requestMagicLink } from "./src/api";
import { onNotificationOpened, registerForOwnerNotifications } from "./src/notifications";

const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  Constants.expoConfig?.extra?.apiBaseUrl ??
  "https://whoops-tag.vercel.app";

type ActionButtonProps = {
  title: string;
  onPress: () => void;
  tone?: "dark" | "quiet";
  disabled?: boolean;
};

function ActionButton({ title, onPress, tone = "dark", disabled = false }: ActionButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.actionButton,
        tone === "quiet" && styles.quietButton,
        pressed && styles.actionButtonPressed,
        disabled && styles.actionButtonDisabled,
      ]}
    >
      <Text style={[styles.actionButtonText, tone === "quiet" && styles.quietButtonText]}>{title}</Text>
    </Pressable>
  );
}

type AuthMode = "register" | "login";

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
  const loadingMessages = useRef(false);
  const messageRefs = useRef<Set<string>>(new Set());
  const sendingMessage = useRef(false);
  const [newLabel, setNewLabel] = useState("");
  const [tagLinks, setTagLinks] = useState<Record<string, string>>({});
  const [ready, setReady] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("register");
  const [loginToken, setLoginToken] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [notificationStatus, setNotificationStatus] = useState("Live inbox refresh is active.");
  const api = useMemo(() => (session ? new OwnerApi({ baseUrl: API_BASE, sessionToken: session }) : null), [session]);

  const knownInboxRefs = useRef<Set<string>>(new Set());
  const inboxInitialized = useRef(false);

  useEffect(() => {
    let active = true;
    void SecureStore.getItemAsync("owner_session")
      .then(async (stored) => {
        if (stored) {
          const savedLinks = await SecureStore.getItemAsync("recording_links");
          if (savedLinks) {
            const recording = await bootstrapRecording(API_BASE);
            if (!active) return;
            const links = Object.fromEntries(recording.items.map((item) => [item.item_ref, item.finder_url]));
            await SecureStore.setItemAsync("owner_session", recording.session_token);
            await SecureStore.setItemAsync("recording_links", JSON.stringify(links));
            setTagLinks(links);
            setSession(recording.session_token);
            return;
          }
          try {
            await new OwnerApi({ baseUrl: API_BASE, sessionToken: stored }).listItems();
            if (active) setSession(stored);
            return;
          } catch {
            await SecureStore.deleteItemAsync("owner_session");
          }
        }
        const recording = await bootstrapRecording(API_BASE);
        if (!active) return;
        const links = Object.fromEntries(recording.items.map((item) => [item.item_ref, item.finder_url]));
        await SecureStore.setItemAsync("owner_session", recording.session_token);
        await SecureStore.setItemAsync("recording_links", JSON.stringify(links));
        setTagLinks(links);
        setSession(recording.session_token);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, []);


  async function refresh() {
    if (!api) return;
    const [nextItems, nextInbox] = await Promise.all([api.listItems(), api.inbox()]);
    const newEvents = nextInbox.filter((event) => !knownInboxRefs.current.has(event.found_ref));
    const [event] = newEvents;
    if (inboxInitialized.current && event) {
      Alert.alert("New found report", `${event.label} was just found.\n\nWanna join chat?`, [
        { text: "Not now", style: "cancel" },
        { text: "Join chat", onPress: () => setSelected(event) },
      ]);
    }
    knownInboxRefs.current = new Set(nextInbox.map((event) => event.found_ref));
    inboxInitialized.current = true;
    setItems(nextItems);
    setInbox(nextInbox);
  }


  useEffect(() => {
    if (!api) return;
    void refresh().catch((error: Error) => Alert.alert("Could not load account", error.message));
    void registerForOwnerNotifications()
      .then((pushToken) => {
        if (!pushToken) {
          setNotificationStatus("Live inbox refresh is active; system push is disabled for this APK.");
          return;
        }
        setNotificationStatus("System notifications enabled.");
        return api.registerDevice(pushToken, Platform.OS === "ios" ? "ios" : "android");
      })
      .catch((error: Error) => {
        console.warn("System notifications unavailable:", error.message);
        setNotificationStatus("Live inbox refresh is active; system push is not configured for this APK.");
      });
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
    messageRefs.current.clear();
    const load = async () => {
      if (loadingMessages.current) return;
      loadingMessages.current = true;
      try {
        const next = await api.messages(selected.conversation_ref, lastMessage.current);
        if (active && next.length) {
          lastMessage.current = next.at(-1)?.created_at ?? lastMessage.current;
          const unseen = next.filter((message) => !messageRefs.current.has(message.message_ref));
          unseen.forEach((message) => messageRefs.current.add(message.message_ref));
          if (unseen.length) setMessages((current) => [...current, ...unseen]);
        }
      } finally {
        loadingMessages.current = false;
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

  async function requestLogin() {
    try {
      const result = await requestMagicLink(API_BASE, email);
      setLoginToken(result.token);
      setAuthMessage("One-time sign-in token ready. Tap Continue to sign in.");
    } catch (error) {
      Alert.alert("Could not send magic link", (error as Error).message);
    }
  }

  async function finishLogin() {
    try {
      const result = await consumeMagicLink(API_BASE, loginToken);
      await SecureStore.setItemAsync("owner_session", result.token);
      setSession(result.token);
      setLoginToken("");
      setAuthMessage("");
    } catch (error) {
      Alert.alert("Could not sign in", (error as Error).message);
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
    if (!api || !selected || !newMessage.trim() || sendingMessage.current) return;
    sendingMessage.current = true;
    try {
      const message = await api.sendMessage(selected.conversation_ref, newMessage.trim());
      lastMessage.current = message.created_at;
      messageRefs.current.add(message.message_ref);
      setMessages((current) => [...current, message]);
      setNewMessage("");
    } catch (error) {
      Alert.alert("Could not send message", (error as Error).message);
    } finally {
      sendingMessage.current = false;
    }
  }

  async function shareTagUrl(url: string) {
    try {
      await Share.share({ message: url });
    } catch (error) {
      Alert.alert("Could not share tag link", (error as Error).message);
    }
  }

  async function shareTagLink(itemRef: string) {
    const url = tagLinks[itemRef];
    if (url) await shareTagUrl(url);
  }

  async function provisionTag(itemRef: string) {
    if (!api) return;
    try {
      const tag = await api.provisionTag(itemRef);
      setTagLinks((current) => ({ ...current, [itemRef]: tag.finder_url }));
      Alert.alert("Tag ready", "Share the tag link to print a QR label or write the NFC tag.", [
        { text: "Share tag link", onPress: () => void shareTagUrl(tag.finder_url) },
        { text: "Done", style: "cancel" },
      ]);
    } catch (error) {
      Alert.alert("Could not provision tag", (error as Error).message);
    }
  }

  if (!ready) return <SafeAreaView style={styles.safe}><Text style={styles.muted}>Loading owner session…</Text></SafeAreaView>;

  if (!session) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.shell}>
          <Text style={styles.eyebrow}>WHOOPS TAG</Text>
          <Text style={styles.title}>Keep your things findable.</Text>
          <Text style={styles.muted}>Private owner access for your recovery inbox.</Text>
          <View style={styles.authTabs}>
              <ActionButton title="Register" tone={authMode === "register" ? "dark" : "quiet"} onPress={() => { setAuthMode("register"); setAuthMessage(""); }} />
              <ActionButton title="Log in" tone={authMode === "login" ? "dark" : "quiet"} onPress={() => { setAuthMode("login"); setAuthMessage(""); }} />
          </View>
          {authMode === "register" ? (
            <>
              <TextInput style={styles.input} placeholder="Your name" value={name} onChangeText={setName} />
              <TextInput style={styles.input} placeholder="Email" keyboardType="email-address" autoCapitalize="none" value={email} onChangeText={setEmail} />
              <ActionButton title="Create owner account" onPress={() => void signUp()} />
            </>
          ) : (
            <>
              <TextInput style={styles.input} placeholder="Email" keyboardType="email-address" autoCapitalize="none" value={email} onChangeText={setEmail} />
              <ActionButton title="Send magic link" onPress={() => void requestLogin()} />
              {authMessage ? <Text style={styles.muted}>{authMessage}</Text> : null}
              {loginToken ? (
                <>
                  <TextInput style={styles.input} placeholder="Magic link token" autoCapitalize="none" value={loginToken} onChangeText={setLoginToken} />
                  <ActionButton title="Continue to owner account" onPress={() => void finishLogin()} />
                </>
              ) : null}
            </>
          )}
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <FlatList
        contentContainerStyle={styles.shell}
        keyboardShouldPersistTaps="handled"
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
                placeholder="Ducky"
                value={newLabel}
                onChangeText={setNewLabel}
              />
              <ActionButton title="Add" onPress={() => void addItem()} />
            </View>
            <Text style={styles.section}>Found reports</Text>
            {inbox.map((event) => (
              <View style={styles.card} key={event.found_ref}>
                <Text style={styles.cardTitle}>{event.label}</Text>
                <Text style={styles.muted}>
                  {event.place}{event.note ? ` — ${event.note}` : ""}
                </Text>
                <ActionButton
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
                  <ActionButton title="Send" onPress={() => void send()} />
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
            {tagLinks[item.item_ref] && (
              <>
                <Text style={styles.muted}>Tag ready for NFC / QR.</Text>
                <ActionButton
                  title="Share tag link"
                  tone="quiet"
                  onPress={() => void shareTagLink(item.item_ref)}
                />
              </>
            )}
            <ActionButton
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
  safe: { flex: 1, backgroundColor: "#f3f1ec" },
  shell: { width: "100%", maxWidth: 720, alignSelf: "center", padding: 24, gap: 12 },
  authTabs: { flexDirection: "row", gap: 8, marginVertical: 12 },
  eyebrow: { color: "#b24b2b", fontWeight: "700", letterSpacing: 2.5, fontSize: 12 },
  title: { fontFamily: "Georgia", fontSize: 40, fontWeight: "400", lineHeight: 44, color: "#171716", marginVertical: 4 },
  section: { fontFamily: "Georgia", fontSize: 24, fontWeight: "400", color: "#171716", marginTop: 22 },
  muted: { color: "#6b6a64", lineHeight: 22 },
  input: { backgroundColor: "#fbfaf7", color: "#171716", borderColor: "#c7c3ba", borderWidth: 1, borderRadius: 11, padding: 13, marginVertical: 6 },
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  card: { backgroundColor: "#fbfaf7", borderColor: "#d9d4ca", borderWidth: 1, borderRadius: 18, padding: 18, marginVertical: 6, gap: 8, shadowColor: "#171716", shadowOpacity: 0.05, shadowRadius: 10, shadowOffset: { width: 0, height: 4 }, elevation: 2 },
  cardTitle: { fontFamily: "Georgia", fontSize: 21, fontWeight: "400", color: "#171716" },
  message: { backgroundColor: "#eeece6", color: "#171716", padding: 10, borderRadius: 11 },
  actionButton: { backgroundColor: "#171716", borderRadius: 999, paddingHorizontal: 16, paddingVertical: 12, alignItems: "center", justifyContent: "center" },
  quietButton: { backgroundColor: "transparent", borderColor: "#c7c3ba", borderWidth: 1 },
  actionButtonText: { color: "#fbfaf7", fontWeight: "700" },
  quietButtonText: { color: "#171716" },
  actionButtonPressed: { opacity: 0.78 },
  actionButtonDisabled: { opacity: 0.45 },
});
