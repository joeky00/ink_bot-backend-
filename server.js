const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
const port = 3000;

const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;

app.use(cors());
app.use(express.json());

app.post("/chat", async (req, res) => {
  const userInput = req.body.message;

  try {
    const response = await axios.post(
      "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
      { inputs: userInput },
      {
        headers: {
          Authorization: `Bearer ${HF_API_KEY}`,
        },
      }
    );

    const botReply = response.data?.[0]?.generated_text || "Sorry, no reply.";
    res.json({ message: botReply });
  } catch (error) {
    console.error("Error:", error.message);
    res.status(500).json({ message: "Something went wrong." });
  }
});

app.listen(port, () => {
  console.log(`Ink Bot is running on port ${port}
         `);
});
