// src/components/Layout/MainLayout.jsx
import React, { useState } from "react";
import { Box, Drawer, IconButton, Typography } from "@mui/material";
import { FaBars } from "react-icons/fa";
// import ChatSidebar from "./Chat/ChatSidebar";
import "../css/layout.css";

const MainLayout = ({ children }) => {
  const [open, setOpen] = useState(true);

  return (
    <Box className="layout-root">
      {/* <Drawer
        variant="persistent"
        anchor="left"
        open={open}
        className="drawer"
        PaperProps={{ className: "drawer-paper" }}
      >
        {/* <ChatSidebar /> 
      </Drawer> */}

      <Box className="main-content">
        <Box className="layout-header">
          <IconButton onClick={() => setOpen(!open)} className="menu-btn">
            <FaBars />
          </IconButton>
          <Typography variant="h6">AI Course Assistant</Typography>
        </Box>
        <Box className="layout-body">{children}</Box>
      </Box>
    </Box>
  );
};

export default MainLayout;
