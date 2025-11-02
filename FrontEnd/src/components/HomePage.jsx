import React, { useState, useEffect } from "react"
import {
    Container,
    Box,
    AppBar,
    Toolbar,
    Typography,
    Button,
    Grid,
    Card,
    CardContent,
    useTheme,
    useMediaQuery,
    Modal,
    TextField,
    Link,
    IconButton,
    Menu,
    MenuItem,
} from "@mui/material"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import {
    faBrain,
    faBook,
    faPalette,
    faFilm,
    faStar,
    faGear,
    faRocket,
    faArrowRight,
    faArrowDown,
    faChevronDown,
} from "@fortawesome/free-solid-svg-icons"
import "../css/home.css"
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { redirect } from "react-router-dom"

export default function HomePage() {
    const backendUrl = import.meta.env.VITE_BACKEND_URL;
    const theme = useTheme()
    const isMobile = useMediaQuery(theme.breakpoints.down("md"))
    const [openModal, setOpenModal] = useState(null); // "Signup" | "Login" | "Reset" | null
    const [formData, setFormData] = useState({
        name: "",
        username: "",
        password: "",
        confirmPassword: "",
    });
    const [error, setError] = useState("");
    const [anchorEl, setAnchorEl] = useState(null);
    const [user, setUser] = useState(null);
    const isMenuOpen = Boolean(anchorEl);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleClose = () => {
        setOpenModal(null);
        setFormData({ username: "", password: "", confirmPassword: "" });
        setError("");
    };

    const checkLoginStatus = async () => {
        const token = localStorage.getItem("token");
        console.log(token);
        const res = await fetch(`${backendUrl}profile`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
        });
        const data = await res.json();
        console.log(data);
        return data;
    }

    useEffect(() => {
        const getUser = async () => {
            const userData = await checkLoginStatus();
            console.log("User Data:", userData);
            if (userData.username) setUser(userData.username);
        };
        getUser();
    }, []);

    const handleMenuOpen = (event) => setAnchorEl(event.currentTarget);
    const handleMenuClose = () => setAnchorEl(null);

    const handleLogout = () => {
        localStorage.removeItem("token");
        setUser(null);
        handleMenuClose();
    };

    const handleSubmit = async (type) => {
        setError("");

        // Basic validation
        if (type === "Signup" && formData.password !== formData.confirmPassword) {
            setError("Passwords do not match!");
            return;
        }

        try {
            const endpointMap = {
                Signup: `${backendUrl}signup`,
                Login: `${backendUrl}login`,
                Reset: `${backendUrl}forget-password`,
            };
            console.log(type);
            console.log(endpointMap[type]);
            const res = await fetch(endpointMap[type], {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            const data = await res.json();
            console.log(data);

            if (!res.ok) {
                toast.error('Something went wrong!');
                return;
            }

            toast.success(`${type} successful!`);
            handleClose();
            if (type !== "Reset") {
                localStorage.setItem("token", data.access_token);
                redirect();
            } else {
                setOpenModal("Login");
            }
        } catch (err) {
            setError(err.message);
        }
    };

    const redirect = async () => {
        const data = await checkLoginStatus();
        if (!data.username) {
            alert("Please log in to access the chat.");
            setOpenModal("Login");
            return;
        }
        window.location.href = "/chat";
    };

    const renderModal = (type) => (
        <Modal open={openModal === type} onClose={handleClose}>
            <Box
                sx={{
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                    width: 360,
                    bgcolor: "#d5d0d0ff",
                    borderRadius: 2,
                    boxShadow: 24,
                    p: 4,
                }}
            >
                <Typography variant="h6" sx={{ mb: 2, textAlign: "center", color: "#333", fontWeight: "bold" }}>
                    {type === "Signup"
                        ? "Sign Up"
                        : type === "Login"
                            ? "Log In"
                            : "Forgot Password"}
                </Typography>

                {type === "Signup" && (
                    <TextField
                        fullWidth
                        label="Name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        sx={{
                            mb: 2,
                        }}
                    />
                )}

                <TextField
                    fullWidth
                    label="Username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    sx={{
                        mb: 2,
                    }}
                />

                <TextField
                    fullWidth
                    label="Password"
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    sx={{ mb: 2 }}
                />

                {type === "Signup" && (
                    <TextField
                        fullWidth
                        label="Confirm Password"
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        sx={{ mb: 2 }}
                    />
                )}

                {error && (
                    <Typography color="error" variant="body2" sx={{ mb: 2 }}>
                        {error}
                    </Typography>
                )}

                <Button
                    variant="contained"
                    fullWidth
                    onClick={() => handleSubmit(type)}
                    sx={{ mb: 2 }}
                >
                    {type === "Signup"
                        ? "Sign Up"
                        : type === "Login"
                            ? "Log In"
                            : "Reset Password"}
                </Button>

                {/* Footer Links */}
                <Box textAlign="center">
                    {type === "Signup" && (
                        <Typography color="black">Already have an account?{" "}
                            <Link
                                href="#"
                                onClick={() => {
                                    handleClose();
                                    setOpenModal("Login");
                                }}
                            >
                                Log In Here
                            </Link>
                        </Typography>
                    )}

                    {type === "Login" && (
                        <>
                            <Typography color="black"
                                sx={{ display: "block", mb: 1 }}>Don't have an account?{" "}
                                <Link
                                    href="#"
                                    onClick={() => {
                                        handleClose();
                                        setOpenModal("Signup");
                                    }}
                                >
                                    Register Now
                                </Link>
                            </Typography>
                            <Typography color="black">Forgot your password?{" "}
                                <Link
                                    href="#"
                                    onClick={() => {
                                        handleClose();
                                        setOpenModal("Reset");
                                    }}
                                >
                                    Reset Here
                                </Link>
                            </Typography>
                        </>
                    )}

                    {type === "Reset" && (
                        <Link
                            href="#"
                            onClick={() => {
                                handleClose();
                                setOpenModal("Login");
                            }}
                        >
                            Back to Login
                        </Link>
                    )}
                </Box>
            </Box>
        </Modal>
    );

    return (
        <Box className="home-container">
            {/* Header */}
            <AppBar position="sticky" className="home-header">
                <Toolbar className="header-content">
                    <Box className="logo">
                        <FontAwesomeIcon icon={faBrain} className="logo-icon" />
                        <Typography variant="h6" className="logo-text">
                            HackTutor
                        </Typography>
                    </Box>
                    {!isMobile && (
                        <Box className="nav-links" sx={{ display: "flex", alignItems: "center", gap: 3 }}>
                            <a href="#features" className="nav-link">
                                Features
                            </a>
                            <a href="#how-it-works" className="nav-link">
                                How It Works
                            </a>

                            {user && (
                                <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 3 }}>
                                    <Typography variant="body1" sx={{ color: "#fff", fontWeight: 500 }}>
                                        Hi, {user}
                                    </Typography>
                                    <IconButton color="inherit" onClick={handleMenuOpen}>
                                        <FontAwesomeIcon icon={faChevronDown} />
                                    </IconButton>

                                    <Menu
                                        anchorEl={anchorEl}
                                        open={isMenuOpen}
                                        onClose={handleMenuClose}
                                        slotProps={{
                                            paper: {
                                                sx: {
                                                    bgcolor: "#2e2e2e",
                                                    color: "#fff",
                                                    borderRadius: 2,
                                                    boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
                                                },
                                            },
                                        }}
                                    >
                                        <MenuItem
                                            onClick={handleLogout}
                                            sx={{
                                                "&:hover": { bgcolor: "#424242" },
                                            }}
                                        >
                                            Logout
                                        </MenuItem>
                                    </Menu>
                                </Box>
                            )}
                        </Box>
                    )}
                </Toolbar>
            </AppBar>
            <Toaster position="top-right" reverseOrder={false} />
            {/* Hero Section */}
            <Box className="hero">
                <Box className="hero-content">
                    <Typography variant="h2" className="hero-title">
                        Your AI-Powered <span className="gradient-text">Learning Companion</span>
                    </Typography>
                    <Typography variant="h6" className="hero-subtitle">
                        Master any topic with personalized explanations, diagrams, and step-by-step guidance tailored just for you.
                    </Typography>
                    <Box className="hero-buttons" justifyContent={"center"}>
                        <Button variant="contained" className="btn btn-primary" onClick={redirect}>
                            Chat Now
                        </Button>
                        {!user && (
                            <>
                                <Button variant="outlined" className="btn btn-secondary" onClick={() => setOpenModal("Signup")}>
                                    Sign Up
                                </Button>
                                <Button className="btn btn-secondary" onClick={() => setOpenModal("Login")}>
                                    Log In
                                </Button>
                            </>
                        )}
                    </Box>
                </Box>

                <Box className="hero-visual">
                    <Card className="floating-card card-1">
                        <CardContent className="card-content">
                            <FontAwesomeIcon icon={faBook} className="card-icon" />
                            <Typography>Instant Explanations</Typography>
                        </CardContent>
                    </Card>
                    <Card className="floating-card card-2">
                        <CardContent className="card-content">
                            <FontAwesomeIcon icon={faPalette} className="card-icon" />
                            <Typography>Visual Diagrams</Typography>
                        </CardContent>
                    </Card>
                    <Card className="floating-card card-3">
                        <CardContent className="card-content">
                            <FontAwesomeIcon icon={faFilm} className="card-icon" />
                            <Typography>Video Summaries</Typography>
                        </CardContent>
                    </Card>
                </Box>
            </Box>

            {/* Features Section */}
            <Box id="features" className="features">
                <Typography variant="h4" className="section-title" sx={{ mb: 3 }}>
                    Why Choose HackTutor?
                </Typography>
                <Grid container spacing={3} className="features-grid" justifyContent="center" alignItems="stretch">
                    {/* What It Is */}
                    <Grid item xs={12} sm={6} md={4}>
                        <Card className="feature-card">
                            <CardContent>
                                <Box className="feature-icon">
                                    <FontAwesomeIcon icon={faStar} />
                                </Box>
                                <Typography variant="h6">What It Is</Typography>
                                <Typography variant="body2">
                                    An intelligent teaching assistant that understands your learning style and adapts content to help you
                                    master complex topics faster.
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* How It Works */}
                    <Grid item xs={12} sm={6} md={4}>
                        <Card className="feature-card">
                            <CardContent>
                                <Box className="feature-icon">
                                    <FontAwesomeIcon icon={faGear} />
                                </Box>
                                <Typography variant="h6">How It Works</Typography>
                                <Typography variant="body2">
                                    We combine AI-powered content curation with real-time feedback to create a personalized learning
                                    experience that evolves with you.
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* What Sets Us Apart */}
                    <Grid item xs={12} sm={6} md={4}>
                        <Card className="feature-card">
                            <CardContent>
                                <Box className="feature-icon">
                                    <FontAwesomeIcon icon={faRocket} />
                                </Box>
                                <Typography variant="h6">What Sets Us Apart</Typography>
                                <Typography variant="body2">
                                    Beyond simple Q&A, we provide comprehensive learning paths with multiple formats to ensure deep
                                    understanding and retention.
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Box>

            {/* How It Works Section */}
            <Box id="how-it-works" className="how-it-works">
                <Typography variant="h4" className="section-title" sx={{ mb: 3 }}>
                    Your Learning Journey in 4 Steps
                </Typography>
                <Box className="steps-container">
                    {/* Step 1 */}
                    <Box className="step">
                        <Box className="step-number">1</Box>
                        <Box className="step-content">
                            <Typography variant="subtitle1">Enter Your Topic</Typography>
                            <Typography variant="caption">Tell us what you want to learn about in your own words</Typography>
                        </Box>
                    </Box>

                    <Box className="step-arrow">
                        <FontAwesomeIcon icon={isMobile ? faArrowDown : faArrowRight} />
                    </Box>

                    {/* Step 2 */}
                    <Box className="step">
                        <Box className="step-number">2</Box>
                        <Box className="step-content">
                            <Typography variant="subtitle1">AI Curates Content</Typography>
                            <Typography variant="caption">
                                Our assistant gathers the best learning materials for your topic
                            </Typography>
                        </Box>
                    </Box>

                    <Box className="step-arrow">
                        <FontAwesomeIcon icon={isMobile ? faArrowDown : faArrowRight} />
                    </Box>

                    {/* Step 3 */}
                    <Box className="step">
                        <Box className="step-number">3</Box>
                        <Box className="step-content">
                            <Typography variant="subtitle1">Get Rich Summaries</Typography>
                            <Typography variant="caption">Receive summaries, diagrams, and video explanations instantly</Typography>
                        </Box>
                    </Box>

                    <Box className="step-arrow">
                        <FontAwesomeIcon icon={isMobile ? faArrowDown : faArrowRight} />
                    </Box>

                    {/* Step 4 */}
                    <Box className="step">
                        <Box className="step-number">4</Box>
                        <Box className="step-content">
                            <Typography variant="subtitle1">Continue Learning</Typography>
                            <Typography variant="caption">Chat with the assistant for clarifications and deeper insights</Typography>
                        </Box>
                    </Box>
                </Box>
            </Box>

            {/* CTA Section */}
            <Box className="cta-section">
                <Typography variant="h4">Ready to Transform Your Learning?</Typography>
                <Typography variant="body1">Join thousands of students already mastering new skills with HackTutor</Typography>
                <Box className="cta-buttons">
                    <Button variant="contained" className="btn btn-primary btn-large" onClick={() => redirect()}>
                        Get Started for Free
                    </Button>
                    <Button variant="outlined" className="btn btn-outline btn-large" onClick={() => setOpenModal("Signup")}>
                        Register Now
                    </Button>
                </Box>
            </Box>

            {renderModal("Signup")}
            {renderModal("Login")}
            {renderModal("Reset")}

            {/* Footer */}
            <Box component="footer" className="footer">
                <Container className="footer-content">
                    <Typography variant="body2">&copy; 2025 HackTutor. All rights reserved.</Typography>
                    <Box className="footer-links">
                        <a href="#privacy">Privacy Policy</a>
                        <a href="#terms">Terms of Service</a>
                        <a href="#contact">Contact Us</a>
                    </Box>
                </Container>
            </Box>

        </Box>
    )
}
