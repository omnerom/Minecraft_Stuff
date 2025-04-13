import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.time.Instant;

public class FishBot {

    private final Deque<String> recentLines = new ArrayDeque<>(3);
    private final Deque<String> contextLines = new ArrayDeque<>(10);
    private long lastQuestionTime = 0;
    private long lastMessageTime = 0;
    private final Pattern fishbotPattern = Pattern.compile("\\bhey fishbot\\b", Pattern.CASE_INSENSITIVE);
    private final Pattern connectedPattern = Pattern.compile("is swimming with us!", Pattern.CASE_INSENSITIVE);

    public static void main(String[] args) {
        FishBot bot = new FishBot();
        bot.run();
    }

    public void run() {
        System.out.println("FishBot is online.");
        monitorLogFile("path/to/latest.log");
    }

    public void monitorLogFile(String filePath) {
        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = reader.readLine()) != null) {
                handleLogLine(line);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void handleLogLine(String line) {
        recentLines.add(line);
        if (line.contains("[Chat]")) {
            contextLines.add(cleanMessage(line));
        }

        if (fishbotPattern.matcher(line).find()) {
            handleQuestion(cleanMessage(line));
        }

        if (connectedPattern.matcher(line).find()) {
            handlePlayerJoin(line);
        }
    }

    public void handleQuestion(String message) {
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastQuestionTime < 20000) {
            return; // Cooldown
        }
        lastQuestionTime = currentTime;
        System.out.println("Handling question: " + message);
        // Respond to question
    }

    public void handlePlayerJoin(String line) {
        // Handle player join logic
        System.out.println("Player joined: " + line);
    }

    public String cleanMessage(String message) {
        return message.replace("[I] [Chat] ", "");
    }
}
