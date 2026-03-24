-- Roblox Auto Rejoin Script
-- Tự động check connection và rejoin nếu mất kết nối

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

-- Cấu hình
local CHECK_INTERVAL = 5 -- Kiểm tra kết nối mỗi 5 giây
local REJOIN_DELAY = 10 -- Đợi 10 giây trước khi rejoin
local LOG_PREFIX = "[AutoRejoin]"
local ENABLED = true

-- Biến lưu trạng thái
local lastCheckTime = 0
local isConnected = true
local gameEndedTime = nil

-- In log với timestamp
local function log(message)
    local timestamp = os.date("%H:%M:%S")
    print(LOG_PREFIX .. " [" .. timestamp .. "] " .. message)
end

-- Kiểm tra xem player còn online không
local function checkPlayerOnline()
    local localPlayer = Players.LocalPlayer
    if not localPlayer then
        return false
    end
    
    local character = localPlayer.Character
    if not character then
        return false
    end
    
    local humanoidRootPart = character:FindFirstChild("HumanoidRootPart")
    if not humanoidRootPart then
        return false
    end
    
    return true
end

-- Kiểm tra kết nối đến game
local function checkConnection()
    local connectionState = game:GetState()
    
    -- Kiểm tra các state của Roblox
    if connectionState == Enum.ConnectionState.Connected then
        return true
    end
    
    return false
end

-- Rejoin game
local function rejoinGame()
    log("Đang chuẩn bị rejoin...")
    
    local player = Players.LocalPlayer
    if not player then
        log("ERROR: Không tìm thấy player!")
        return
    end
    
    -- Lấy userId
    local userId = player.UserId
    log("User ID: " .. tostring(userId))
    
    -- Lấy game ID hiện tại
    local placeId = game.PlaceId
    log("Place ID: " .. tostring(placeId))
    
    -- Lấy private server join code nếu có
    local jobId = game.JobId
    log("Job ID: " .. jobId)
    
    -- Teleport lại vào game
    local TeleportService = game:GetService("TeleportService")
    
    if jobId and jobId ~= "" then
        -- Nếu có job ID (trong private server), rejoin vào private server
        log("Rejoin vào private server...")
        pcall(function()
            TeleportService:TeleportToPlaceInstance(placeId, jobId, player)
        end)
    else
        -- Rejoin vào public server
        log("Rejoin vào public server...")
        pcall(function()
            TeleportService:Teleport(placeId, player)
        end)
    end
end

-- Monitor kết nối
local function monitorConnection()
    local currentTime = tick()
    
    -- Kiểm tra mỗi CHECK_INTERVAL giây
    if currentTime - lastCheckTime < CHECK_INTERVAL then
        return
    end
    
    lastCheckTime = currentTime
    
    local playerOnline = checkPlayerOnline()
    local connected = checkConnection()
    
    -- Nếu trước đó online nhưng giờ offline
    if isConnected and not playerOnline then
        if not gameEndedTime then
            gameEndedTime = currentTime
            log("⚠️  Phát hiện mất kết nối!")
            log("Sẽ rejoin sau " .. REJOIN_DELAY .. " giây...")
        elseif currentTime - gameEndedTime >= REJOIN_DELAY then
            log("🔄 Quy trình rejoin bắt đầu!")
            rejoinGame()
            gameEndedTime = nil
        end
        isConnected = false
    elseif not isConnected and playerOnline then
        -- Quay lại online
        log("✅ Kết nối được khôi phục!")
        isConnected = true
        gameEndedTime = nil
    end
end

-- Xử lý khi game kết thúc (khác cách)
local function onGameClose()
    if not ENABLED then
        return
    end
    
    isConnected = false
    if not gameEndedTime then
        gameEndedTime = tick()
        log("⚠️  Game đổi trạng thái, chuẩn bị rejoin...")
    end
end

-- Bắt sự kiện player rời khỏi game
local function setupPlayerMonitoring()
    local player = Players.LocalPlayer
    
    if player then
        -- Monitor character respawn
        local function onCharacterAdded(character)
            log("✅ Character respawned, game còn online")
            isConnected = true
            gameEndedTime = nil
        end
        
        local function onCharacterDied()
            log("💀 Character mất, kiểm tra kết nối...")
            -- Không rejoin ngay, chỉ flag trạng thái
        end
        
        if player.Character then
            onCharacterAdded(player.Character)
        end
        
        player.CharacterAdded:Connect(onCharacterAdded)
        
        local humanoid = player.Character:FindFirstChild("Humanoid")
        if humanoid then
            humanoid.Died:Connect(onCharacterDied)
        end
    end
end

-- Keyboard shortcut để tắt/bật script
local function setupControls()
    UserInputService.InputBegan:Connect(function(input, gameProcessed)
        if gameProcessed then
            return
        end
        
        -- Ctrl + R = Toggle enable/disable
        if input.KeyCode == Enum.KeyCode.R and UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then
            ENABLED = not ENABLED
            local status = ENABLED and "✅ BẬT" or "❌ TẮT"
            log("AutoRejoin " .. status)
        end
        
        -- Ctrl + J = Rejoin ngay lập tức
        if input.KeyCode == Enum.KeyCode.J and UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) then
            log("Rejoin thủ công được kích hoạt bởi người dùng")
            rejoinGame()
        end
    end)
    
    log("Keyboard shortcuts:")
    log("  Ctrl + R = Toggle enable/disable")
    log("  Ctrl + J = Rejoin ngay lập tức")
end

-- Khởi chạy script
local function init()
    log("=== Roblox Auto Rejoin Script Started ===")
    log("Version: 1.0")
    log("Game: " .. game:GetService("MarketplaceService"):GetProductInfo(game.PlaceId).Name)
    log("Player: " .. (Players.LocalPlayer and Players.LocalPlayer.Name or "Unknown"))
    log("Check interval: " .. CHECK_INTERVAL .. " giây")
    log("Rejoin delay: " .. REJOIN_DELAY .. " giây")
    log("")
    
    setupPlayerMonitoring()
    setupControls()
    
    -- Main loop - monitor connection
    RunService.Heartbeat:Connect(function()
        if not ENABLED then
            return
        end
        monitorConnection()
    end)
    
    log("✅ Script đang chạy. Ctrl+R để tắt/bật, Ctrl+J để rejoin ngay.")
end

-- Xử lý khi game đóng
game:BindToClose(function()
    log("Game đang đóng, script kết thúc.")
end)

-- Bắt đầu
init()

-- Notify người dùng (optional)
local function createNotification(text, duration)
    local StarterGui = game:GetService("StarterGui")
    pcall(function()
        StarterGui:SetCore("SendNotification", {
            Title = "AutoRejoin",
            Text = text,
            Duration = duration or 5
        })
    end)
end

createNotification("✅ Auto Rejoin Script Loaded!", 3)
