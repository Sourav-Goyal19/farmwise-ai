import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import axios, { AxiosError } from "axios";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Backend API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

// Define supported languages (matching backend)
const languages = [
  { name: "English", code: "en" },
  { name: "Hindi", code: "hi" },
  { name: "Tamil", code: "ta" },
  { name: "Telugu", code: "te" },
  { name: "Bengali", code: "bn" },
  { name: "Marathi", code: "mr" },
  { name: "Gujarati", code: "gu" },
  { name: "Kannada", code: "kn" },
  { name: "Malayalam", code: "ml" },
];

// Form schema for file upload
const uploadSchema = z.object({
  schemeFile: z
    .instanceof(FileList)
    .refine((files) => files.length === 1, "Please upload one PDF file.")
    .refine(
      (files) => files[0]?.type === "application/pdf",
      "File must be a PDF."
    ),
  language: z.string().min(1, "Please select a language."),
});

// Type for upload form data
type UploadFormData = z.infer<typeof uploadSchema>;

// Form schema for eligibility questions
const eligibilitySchema = z.object({
  answers: z.array(z.enum(["Yes", "No"])),
});

// Type for eligibility form data
type EligibilityFormData = z.infer<typeof eligibilitySchema>;

// Type for upload response
interface UploadResponse {
  success: boolean;
  summary_title?: string;
  summary?: string;
  eligibility_questions?: string;
  language?: string;
  language_code?: string;
  raw?: string;
  error?: string;
}

// Type for eligibility response
interface EligibilityResponse {
  success: boolean;
  is_eligible: boolean;
  result: string;
  error?: string;
}

export default function SchemeUploader() {
  const [summaryData, setSummaryData] = useState<UploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const [isEligibilityLoading, setIsEligibilityLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("en");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [eligibilityResult, setEligibilityResult] =
    useState<EligibilityResponse | null>(null);

  // Upload form
  const uploadForm = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      language: "en",
    },
  });

  const onUploadSubmit = async (data: UploadFormData) => {
    setSummaryData(null);
    setErrorMessage(null);
    setIsLoading(true);
    setAudioUrl(null);
    setEligibilityResult(null);

    try {
      // Upload the file with language
      console.log(
        "Preparing to upload file:",
        data.schemeFile[0].name,
        "with language:",
        data.language
      );
      const formData = new FormData();
      formData.append("scheme_file", data.schemeFile[0]);
      formData.append("language", data.language); // Send language with form data

      const response = await axios.post<UploadResponse>(
        `${API_BASE_URL}/upload_scheme`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("Upload response:", response.data);
      const responseData = response.data;
      if (responseData.success) {
        setSummaryData(responseData);
        setSelectedLanguage(responseData.language_code); // Update to language_code
        setAudioUrl(responseData.audio_url); // Use audio_url (recommended)
      } else {
        setErrorMessage(
          responseData.error || "No summary returned from server."
        );
      }
    } catch (error) {
      console.error("Upload error:", error);
      if (axios.isAxiosError(error)) {
        if (error.code === "ERR_NETWORK") {
          setErrorMessage(
            `Cannot connect to the server. Please ensure the backend is running at ${API_BASE_URL}.`
          );
        } else {
          setErrorMessage(
            (error.response?.data as any)?.error ||
              "Failed to upload scheme. Please try again."
          );
        }
      } else {
        setErrorMessage("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle audio generation
  const handleGenerateAudio = async () => {
    if (!summaryData?.summary) {
      setErrorMessage("No summary available to generate audio.");
      setAudioUrl(null);
      return;
    }

    setErrorMessage(null);
    setAudioUrl(null);
    setIsAudioLoading(true);

    try {
      console.log(
        "Generating audio for summary:",
        summaryData.summary.substring(0, 50) + "..."
      );
      const res = await axios.post(
        `${API_BASE_URL}/generate_audio`,
        {
          summary: summaryData.summary,
          language: selectedLanguage,
        },
        {
          responseType: "blob",
        }
      );

      const blob = new Blob([res.data], { type: "audio/mp3" });
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      console.log("Audio URL generated:", url);
    } catch (error) {
      console.error("Audio generation error:", error);
      if (axios.isAxiosError(error)) {
        if (error.code === "ERR_NETWORK") {
          setErrorMessage(
            `Cannot connect to the server. Please ensure the backend is running at ${API_BASE_URL}.`
          );
        } else {
          setErrorMessage(
            (error.response?.data as any)?.error ||
              "Failed to generate audio. Please try again."
          );
        }
      } else {
        setErrorMessage("An unexpected error occurred while generating audio.");
      }
    } finally {
      setIsAudioLoading(false);
    }
  };

  // Eligibility form
  const eligibilityQuestions = summaryData?.eligibility_questions
    ? summaryData.eligibility_questions.split("\n").filter((q) => q.trim())
    : [];
  const eligibilityForm = useForm<EligibilityFormData>({
    resolver: zodResolver(
      z.object({
        answers: z
          .array(z.enum(["Yes", "No"]))
          .length(eligibilityQuestions.length),
      })
    ),
    defaultValues: {
      answers: eligibilityQuestions.map(() => "No"),
    },
  });

  // Handle eligibility form submission
  const onEligibilitySubmit = async (data: EligibilityFormData) => {
    setErrorMessage(null);
    setIsEligibilityLoading(true);

    try {
      console.log("Submitting eligibility answers:", {
        questions: eligibilityQuestions,
        responses: data.answers,
      });
      const response = await axios.post<EligibilityResponse>(
        `${API_BASE_URL}/check_eligibility`,
        {
          questions: eligibilityQuestions,
          responses: data.answers,
          language: selectedLanguage,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Eligibility response:", response.data);
      if (response.data.success) {
        setEligibilityResult(response.data);
      } else {
        setErrorMessage(response.data.error || "Failed to check eligibility.");
      }
    } catch (error) {
      console.error("Eligibility check error:", error);
      if (axios.isAxiosError(error)) {
        if (error.code === "ERR_NETWORK") {
          setErrorMessage(
            `Cannot connect to the server. Please ensure the backend is running at ${API_BASE_URL}.`
          );
        } else {
          setErrorMessage(
            (error.response?.data as any)?.error ||
              "Failed to check eligibility. Please try again."
          );
        }
      } else {
        setErrorMessage(
          "An unexpected error occurred while checking eligibility."
        );
      }
    } finally {
      setIsEligibilityLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold text-center">
        Upload Government Scheme
      </h1>

      {/* Upload Form */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Scheme PDF</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...uploadForm}>
            <form
              onSubmit={uploadForm.handleSubmit(onUploadSubmit)}
              className="space-y-4"
            >
              {/* Language Selector */}
              <FormField
                control={uploadForm.control}
                name="language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Language</FormLabel>
                    <FormControl>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select a language" />
                        </SelectTrigger>
                        <SelectContent>
                          {languages.map((lang) => (
                            <SelectItem key={lang.code} value={lang.code}>
                              {lang.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* File Input */}
              <FormField
                control={uploadForm.control}
                name="schemeFile"
                render={({ field: { onChange, value, ...rest } }) => (
                  <FormItem>
                    <FormLabel>Upload PDF</FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => {
                          if (e.target.files) {
                            onChange(e.target.files);
                          }
                        }}
                        {...rest}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Submit Button */}
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  "Upload Scheme"
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* Error Message */}
      {errorMessage && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      {/* Summary and Eligibility */}
      {summaryData && (
        <div className="space-y-6">
          {/* Scheme Title */}
          {summaryData.summary_title && (
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl">
                  {summaryData.summary_title}
                </CardTitle>
              </CardHeader>
            </Card>
          )}

          {/* Summary */}
          {summaryData.summary && (
            <Card>
              <CardHeader>
                <CardTitle>Scheme Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 whitespace-pre-wrap">
                  {summaryData.summary}
                </p>
                {/* Audio Generation
                <Button
                  onClick={handleGenerateAudio}
                  disabled={isAudioLoading}
                  className="mt-4 w-full"
                >
                  {isAudioLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating Audio...
                    </>
                  ) : (
                    "Generate Audio"
                  )}
                </Button> */}
                {audioUrl && (
                  <div className="mt-4">
                    <audio controls src={audioUrl} className="w-full">
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Eligibility Questions */}
          {eligibilityQuestions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Check Your Eligibility</CardTitle>
              </CardHeader>
              <CardContent>
                <Form {...eligibilityForm}>
                  <form
                    onSubmit={eligibilityForm.handleSubmit(onEligibilitySubmit)}
                    className="space-y-4"
                  >
                    {eligibilityQuestions.map((question, index) => (
                      <FormField
                        key={index}
                        control={eligibilityForm.control}
                        name={`answers.${index}`}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>{question}</FormLabel>
                            <FormControl>
                              <RadioGroup
                                onValueChange={field.onChange}
                                value={field.value}
                                className="flex space-x-4"
                              >
                                <FormItem className="flex items-center space-x-2">
                                  <FormControl>
                                    <RadioGroupItem value="Yes" />
                                  </FormControl>
                                  <FormLabel className="font-normal">
                                    Yes
                                  </FormLabel>
                                </FormItem>
                                <FormItem className="flex items-center space-x-2">
                                  <FormControl>
                                    <RadioGroupItem value="No" />
                                  </FormControl>
                                  <FormLabel className="font-normal">
                                    No
                                  </FormLabel>
                                </FormItem>
                              </RadioGroup>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    ))}
                    <Button
                      type="submit"
                      className="w-full"
                      disabled={isEligibilityLoading}
                    >
                      {isEligibilityLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Checking Eligibility...
                        </>
                      ) : (
                        "Check Eligibility"
                      )}
                    </Button>
                  </form>
                </Form>
              </CardContent>
            </Card>
          )}

          {/* Eligibility Result */}
          {eligibilityResult && (
            <Card>
              <CardHeader>
                <CardTitle>Eligibility Result</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert
                  variant={
                    eligibilityResult.is_eligible ? "default" : "destructive"
                  }
                >
                  <AlertTitle>
                    {eligibilityResult.is_eligible
                      ? "Eligible"
                      : "Not Eligible"}
                  </AlertTitle>
                  <AlertDescription className="whitespace-pre-wrap">
                    {eligibilityResult.result}
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
