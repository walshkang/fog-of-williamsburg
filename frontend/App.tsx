import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import {
  Borough,
  BoroughDetail,
  CoreScore,
  createOrUpdateUser,
  getBoroughDetail,
  getBoroughs,
  getCoreScore,
} from "./api";
import {
  getChosenBoroughId,
  getOrCreateUserId,
  saveChosenBoroughId,
} from "./storage";

type Screen = "loading" | "onboarding" | "dashboard";

export default function App() {
  const [screen, setScreen] = useState<Screen>("loading");
  const [userId, setUserId] = useState<string | null>(null);
  const [chosenBoroughId, setChosenBoroughId] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      const id = await getOrCreateUserId();
      setUserId(id);
      const storedBoroughId = await getChosenBoroughId();
      if (storedBoroughId != null) {
        setChosenBoroughId(storedBoroughId);
        setScreen("dashboard");
      } else {
        setScreen("onboarding");
      }
    })().catch((err) => {
      console.error("Failed to initialise app", err);
      setScreen("onboarding");
    });
  }, []);

  if (!userId || screen === "loading") {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator />
        <Text style={styles.loadingText}>Loading...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {screen === "onboarding" ? (
        <OnboardingScreen
          userId={userId}
          onCompleted={(boroughId) => {
            setChosenBoroughId(boroughId);
            setScreen("dashboard");
          }}
        />
      ) : (
        <DashboardScreen userId={userId} boroughId={chosenBoroughId} />
      )}
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

type OnboardingProps = {
  userId: string;
  onCompleted: (boroughId: number) => void;
};

function OnboardingScreen({ userId, onCompleted }: OnboardingProps) {
  const [boroughs, setBoroughs] = useState<Borough[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getBoroughs();
        setBoroughs(data);
      } catch (e: any) {
        setError(e?.message ?? "Failed to load boroughs");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const onSelect = async (boroughId: number) => {
    console.log("Tapped borough", boroughId);
    try {
      setSaving(true);
      await createOrUpdateUser({ id: userId, chosenBoroughId: boroughId });
      console.log("User saved");
      await saveChosenBoroughId(boroughId);
      console.log("Borough ID saved locally");
      onCompleted(boroughId);
    } catch (e: any) {
      console.error("Failed to save borough", e);
      setError(e?.message ?? "Failed to save selection");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator />
        <Text style={styles.loadingText}>Loading boroughs...</Text>
      </View>
    );
  }

  return (
    <View style={styles.content}>
      <Text style={styles.title}>Choose your borough</Text>
      {error && <Text style={styles.errorText}>{error}</Text>}
      <FlatList
        data={boroughs}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.boroughButton}
            onPress={() => onSelect(item.id)}
            disabled={saving}
          >
            <Text style={styles.boroughButtonText}>{item.name}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

type DashboardProps = {
  userId: string;
  boroughId: number | null;
};

function DashboardScreen({ userId, boroughId }: DashboardProps) {
  const [detail, setDetail] = useState<BoroughDetail | null>(null);
  const [score, setScore] = useState<CoreScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (boroughId == null) {
      setError("No borough selected.");
      setLoading(false);
      return;
    }

    (async () => {
      try {
        const [d, s] = await Promise.all([
          getBoroughDetail(boroughId),
          getCoreScore(userId),
        ]);
        setDetail(d);
        setScore(s);
      } catch (e: any) {
        setError(e?.message ?? "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    })();
  }, [boroughId, userId]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator />
        <Text style={styles.loadingText}>Loading your map...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  const percent =
    score && Number.isFinite(score.percent_explored)
      ? score.percent_explored.toFixed(2)
      : "0.00";

  return (
    <View style={styles.content}>
      <Text style={styles.title}>
        {percent}% of {detail?.name ?? "your borough"} explored
      </Text>
      <View style={styles.mapPlaceholder}>
        <Text style={styles.mapPlaceholderText}>
          Map placeholder — borough boundary loaded from GeoJSON.
        </Text>
        <Text style={styles.mapSubText}>
          Geometry type:{" "}
          {detail?.geometry ? detail.geometry.type ?? "Unknown" : "None"}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#05050f",
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#05050f",
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#ffffff",
    marginBottom: 16,
  },
  loadingText: {
    marginTop: 12,
    color: "#ffffff",
  },
  errorText: {
    marginBottom: 12,
    color: "#ff6b6b",
  },
  boroughButton: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: "#111827",
    marginBottom: 8,
  },
  boroughButtonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "500",
  },
  mapPlaceholder: {
    marginTop: 24,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1f2937",
    backgroundColor: "#020617",
    padding: 16,
  },
  mapPlaceholderText: {
    color: "#9ca3af",
    marginBottom: 8,
  },
  mapSubText: {
    color: "#6b7280",
    fontSize: 12,
  },
});
