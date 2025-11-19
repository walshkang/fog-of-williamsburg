import AsyncStorage from "@react-native-async-storage/async-storage";

const USER_ID_KEY = "fog.userId";
const BOROUGH_ID_KEY = "fog.chosenBoroughId";

function generateRandomId(): string {
  // Simple random hex-based ID, sufficient for anonymous device identity.
  const bytes = Array.from({ length: 16 }, () =>
    Math.floor(Math.random() * 256)
  );
  return bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function getOrCreateUserId(): Promise<string> {
  const existing = await AsyncStorage.getItem(USER_ID_KEY);
  if (existing) {
    return existing;
  }
  const id = generateRandomId();
  await AsyncStorage.setItem(USER_ID_KEY, id);
  return id;
}

export async function saveChosenBoroughId(id: number): Promise<void> {
  await AsyncStorage.setItem(BOROUGH_ID_KEY, String(id));
}

export async function getChosenBoroughId(): Promise<number | null> {
  const val = await AsyncStorage.getItem(BOROUGH_ID_KEY);
  if (!val) return null;
  const asNum = Number(val);
  return Number.isFinite(asNum) ? asNum : null;
}


