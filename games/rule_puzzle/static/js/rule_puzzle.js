// Rule Puzzle Game JavaScript
class RulePuzzleGame {
    constructor() {
        this.sessionId = null;
        this.gameData = null;
        this.selectedDifficulty = 'medium';
        this.currentScore = 0;
        this.timeRemaining = 300; // 5 minutes
        this.timer = null;
        this.hintsUsed = 0;
        this.vehiclePositions = {};
        this.dropZones = {};
        this.isDragging = false;
        this.draggedVehicle = null;
        
        // Bind methods
        this.handleMouseDown = this.handleMouseDown.bind(this);
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleMouseUp = this.handleMouseUp.bind(this);
        this.handleTouchStart = this.handleTouchStart.bind(this);
        this.handleTouchMove = this.handleTouchMove.bind(this);
        this.handleTouchEnd = this.handleTouchEnd.bind(this);
    }
    
    init() {
        console.log('Initializing Rule Puzzle Game');
        this.setupEventListeners();
        this.showSetupScreen();
    }
    
    setupEventListeners() {
        // Setup screen
        document.querySelectorAll('.difficulty-card').forEach(card => {
            card.addEventListener('click', (e) => this.selectDifficulty(e));
        });
        
        document.getElementById('start-game-btn').addEventListener('click', () => {
            this.startGame();
        });
        
        // Game controls
        document.getElementById('hint-btn').addEventListener('click', () => {
            this.requestHint();
        });
        
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.resetScenario();
        });
        
        document.getElementById('submit-btn').addEventListener('click', () => {
            this.submitSolution();
        });
        
        // Results screen
        document.getElementById('play-again-btn').addEventListener('click', () => {
            this.showSetupScreen();
        });
        
        document.getElementById('back-to-games-btn').addEventListener('click', () => {
            window.location.href = '/games/';
        });
    }
    
    selectDifficulty(event) {
        // Remove previous selection
        document.querySelectorAll('.difficulty-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selection to clicked card
        event.currentTarget.classList.add('selected');
        this.selectedDifficulty = event.currentTarget.dataset.difficulty;
        
        console.log('Selected difficulty:', this.selectedDifficulty);
    }
    
    async startGame() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/games/rule_puzzle/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    difficulty: this.selectedDifficulty
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.sessionId = data.session_data.session_id;
                this.gameData = data.session_data;
                this.timeRemaining = this.gameData.time_limit;
                
                this.setupGameBoard();
                this.showGameScreen();
                this.startTimer();
            } else {
                throw new Error(data.error || 'Failed to start game');
            }
        } catch (error) {
            console.error('Error starting game:', error);
            alert('Feil ved start av spill: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    setupGameBoard() {
        const scenario = this.gameData.scenario;
        const config = this.gameData.scenario_config;
        
        // Update scenario info
        document.getElementById('scenario-title').textContent = `Scenario: ${scenario.name}`;
        document.getElementById('scenario-description').textContent = scenario.description;
        
        // Update rules list
        const rulesList = document.getElementById('scenario-rules-list');
        rulesList.innerHTML = '';
        config.rules.forEach(rule => {
            const li = document.createElement('li');
            li.textContent = rule;
            rulesList.appendChild(li);
        });
        
        // Setup road layout
        this.setupRoadLayout(config.road_layout);
        
        // Setup vehicles
        this.setupVehicles(config.vehicles, config.starting_positions);
        
        // Setup drop zones
        this.setupDropZones(config.road_layout);
        
        // Reset game state
        this.currentScore = 0;
        this.hintsUsed = 0;
        this.updateGameStats();
    }
    
    setupRoadLayout(layout) {
        const roadContainer = document.getElementById('road-layout');
        roadContainer.innerHTML = '';
        roadContainer.className = 'road-container';
        
        // Create road graphics based on layout type
        if (layout.type === 'intersection') {
            this.createIntersectionLayout(roadContainer);
        } else if (layout.type === 'roundabout') {
            this.createRoundaboutLayout(roadContainer);
        } else if (layout.type === 'crossing') {
            this.createCrossingLayout(roadContainer);
        } else if (layout.type === 'highway') {
            this.createHighwayLayout(roadContainer);
        } else if (layout.type === 'merge') {
            this.createMergeLayout(roadContainer);
        } else if (layout.type === 'school_zone') {
            this.createSchoolZoneLayout(roadContainer);
        } else {
            this.createDefaultLayout(roadContainer);
        }
    }
    
    createIntersectionLayout(container) {
        // Horizontal road
        const roadH = document.createElement('div');
        roadH.className = 'road-horizontal';
        container.appendChild(roadH);
        
        // Vertical road
        const roadV = document.createElement('div');
        roadV.className = 'road-vertical';
        container.appendChild(roadV);
        
        // Center intersection
        const center = document.createElement('div');
        center.className = 'road-center';
        container.appendChild(center);
        
        // Add lane markings
        for (let i = 0; i < 20; i++) {
            const marking = document.createElement('div');
            marking.className = 'lane-marking horizontal';
            marking.style.left = (i * 30) + 'px';
            container.appendChild(marking);
        }
        
        for (let i = 0; i < 15; i++) {
            const marking = document.createElement('div');
            marking.className = 'lane-marking vertical';
            marking.style.top = (i * 30) + 'px';
            container.appendChild(marking);
        }
    }
    
    createRoundaboutLayout(container) {
        // Create circular roundabout
        const roundabout = document.createElement('div');
        roundabout.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            width: 150px;
            height: 150px;
            border: 20px solid #374151;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            background: #10b981;
        `;
        container.appendChild(roundabout);
        
        // Add entry/exit roads
        const roads = ['north', 'south', 'east', 'west'];
        roads.forEach((direction, index) => {
            const road = document.createElement('div');
            const angle = index * 90;
            road.style.cssText = `
                position: absolute;
                width: 60px;
                height: 120px;
                background: #374151;
                transform-origin: center bottom;
                transform: rotate(${angle}deg);
            `;
            
            if (direction === 'north') {
                road.style.top = '0';
                road.style.left = '50%';
                road.style.marginLeft = '-30px';
            } else if (direction === 'south') {
                road.style.bottom = '0';
                road.style.left = '50%';
                road.style.marginLeft = '-30px';
            } else if (direction === 'east') {
                road.style.right = '0';
                road.style.top = '50%';
                road.style.marginTop = '-30px';
                road.style.width = '120px';
                road.style.height = '60px';
            } else if (direction === 'west') {
                road.style.left = '0';
                road.style.top = '50%';
                road.style.marginTop = '-30px';
                road.style.width = '120px';
                road.style.height = '60px';
            }
            
            container.appendChild(road);
        });
    }
    
    createCrossingLayout(container) {
        // Main road
        const road = document.createElement('div');
        road.className = 'road-horizontal';
        container.appendChild(road);
        
        // Pedestrian crossing
        const crossing = document.createElement('div');
        crossing.style.cssText = `
            position: absolute;
            top: 40%;
            left: 45%;
            width: 10%;
            height: 20%;
            background: repeating-linear-gradient(
                90deg,
                white 0px,
                white 10px,
                transparent 10px,
                transparent 20px
            );
        `;
        container.appendChild(crossing);
        
        // Traffic light
        const trafficLight = document.createElement('div');
        trafficLight.style.cssText = `
            position: absolute;
            top: 20%;
            left: 45%;
            width: 20px;
            height: 60px;
            background: #1f2937;
            border-radius: 10px;
        `;
        container.appendChild(trafficLight);
    }
    
    createHighwayLayout(container) {
        // Multiple lanes
        for (let i = 0; i < 3; i++) {
            const lane = document.createElement('div');
            lane.style.cssText = `
                position: absolute;
                top: ${30 + i * 25}%;
                left: 0;
                width: 100%;
                height: 20%;
                background: #374151;
                border-top: 2px dashed white;
            `;
            container.appendChild(lane);
        }
        
        // Shoulder
        const shoulder = document.createElement('div');
        shoulder.style.cssText = `
            position: absolute;
            top: 15%;
            left: 0;
            width: 100%;
            height: 10%;
            background: #6b7280;
        `;
        container.appendChild(shoulder);
    }
    
    createMergeLayout(container) {
        // Main road
        const mainRoad = document.createElement('div');
        mainRoad.style.cssText = `
            position: absolute;
            top: 40%;
            left: 0;
            width: 70%;
            height: 20%;
            background: #374151;
        `;
        container.appendChild(mainRoad);
        
        // Merge lane
        const mergeLane = document.createElement('div');
        mergeLane.style.cssText = `
            position: absolute;
            top: 65%;
            right: 0;
            width: 50%;
            height: 15%;
            background: #374151;
            transform: skew(-30deg);
            transform-origin: bottom right;
        `;
        container.appendChild(mergeLane);
    }
    
    createSchoolZoneLayout(container) {
        // Main road
        const road = document.createElement('div');
        road.className = 'road-horizontal';
        container.appendChild(road);
        
        // School building
        const school = document.createElement('div');
        school.style.cssText = `
            position: absolute;
            top: 10%;
            right: 10%;
            width: 30%;
            height: 25%;
            background: #dc2626;
            border-radius: 8px;
        `;
        school.innerHTML = '<div style="color: white; text-align: center; line-height: 60px; font-size: 14px;">🏫 SKOLE</div>';
        container.appendChild(school);
        
        // Speed limit sign
        const speedSign = document.createElement('div');
        speedSign.style.cssText = `
            position: absolute;
            top: 20%;
            left: 20%;
            width: 40px;
            height: 40px;
            background: white;
            border: 3px solid red;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        `;
        speedSign.textContent = '30';
        container.appendChild(speedSign);
    }
    
    createDefaultLayout(container) {
        // Simple street layout
        const road = document.createElement('div');
        road.className = 'road-horizontal';
        container.appendChild(road);
    }
    
    setupVehicles(vehicles, startingPositions) {
        const vehiclesContainer = document.getElementById('vehicles-container');
        vehiclesContainer.innerHTML = '';
        
        vehicles.forEach(vehicleType => {
            const vehicle = this.createVehicleElement(vehicleType, startingPositions[vehicleType]);
            vehiclesContainer.appendChild(vehicle);
            
            // Store initial position
            this.vehiclePositions[vehicleType] = {
                x: startingPositions[vehicleType].x,
                y: startingPositions[vehicleType].y,
                placed: false
            };
        });
    }
    
    createVehicleElement(vehicleType, position) {
        const vehicleConfig = window.vehicles[vehicleType];
        const vehicle = document.createElement('div');
        
        vehicle.className = 'vehicle';
        vehicle.dataset.vehicleType = vehicleType;
        vehicle.style.left = position.x + 'px';
        vehicle.style.top = position.y + 'px';
        vehicle.style.backgroundColor = vehicleConfig.color;
        vehicle.innerHTML = vehicleConfig.icon;
        vehicle.title = vehicleConfig.name;
        
        // Add drag functionality
        vehicle.addEventListener('mousedown', this.handleMouseDown);
        vehicle.addEventListener('touchstart', this.handleTouchStart, { passive: false });
        
        return vehicle;
    }
    
    setupDropZones(layout) {
        const dropZonesContainer = document.getElementById('drop-zones');
        dropZonesContainer.innerHTML = '';
        
        // Create drop zones based on layout type
        const zones = this.getDropZonesForLayout(layout);
        
        zones.forEach((zone, index) => {
            const dropZone = document.createElement('div');
            dropZone.className = 'drop-zone';
            dropZone.dataset.zoneId = `zone_${index}`;
            dropZone.style.left = zone.x + 'px';
            dropZone.style.top = zone.y + 'px';
            dropZone.textContent = zone.label;
            
            dropZonesContainer.appendChild(dropZone);
            
            this.dropZones[`zone_${index}`] = {
                element: dropZone,
                occupied: false,
                vehicle: null
            };
        });
    }
    
    getDropZonesForLayout(layout) {
        const boardWidth = 800; // Adjust based on actual game board width
        const boardHeight = 400; // Adjust based on actual game board height
        
        if (layout.type === 'intersection') {
            return [
                { x: boardWidth * 0.2, y: boardHeight * 0.3, label: 'Nord' },
                { x: boardWidth * 0.7, y: boardHeight * 0.3, label: 'Øst' },
                { x: boardWidth * 0.7, y: boardHeight * 0.7, label: 'Sør' },
                { x: boardWidth * 0.2, y: boardHeight * 0.7, label: 'Vest' },
                { x: boardWidth * 0.45, y: boardHeight * 0.45, label: 'Sentrum' }
            ];
        } else if (layout.type === 'roundabout') {
            return [
                { x: boardWidth * 0.45, y: boardHeight * 0.1, label: 'Inngang N' },
                { x: boardWidth * 0.8, y: boardHeight * 0.45, label: 'Inngang Ø' },
                { x: boardWidth * 0.45, y: boardHeight * 0.8, label: 'Inngang S' },
                { x: boardWidth * 0.1, y: boardHeight * 0.45, label: 'Inngang V' },
                { x: boardWidth * 0.35, y: boardHeight * 0.35, label: 'I rundkjøring' },
                { x: boardWidth * 0.55, y: boardHeight * 0.55, label: 'I rundkjøring' }
            ];
        } else {
            // Default zones
            return [
                { x: boardWidth * 0.2, y: boardHeight * 0.3, label: 'Posisjon 1' },
                { x: boardWidth * 0.4, y: boardHeight * 0.3, label: 'Posisjon 2' },
                { x: boardWidth * 0.6, y: boardHeight * 0.3, label: 'Posisjon 3' },
                { x: boardWidth * 0.8, y: boardHeight * 0.3, label: 'Posisjon 4' },
                { x: boardWidth * 0.2, y: boardHeight * 0.7, label: 'Posisjon 5' },
                { x: boardWidth * 0.4, y: boardHeight * 0.7, label: 'Posisjon 6' },
                { x: boardWidth * 0.6, y: boardHeight * 0.7, label: 'Posisjon 7' },
                { x: boardWidth * 0.8, y: boardHeight * 0.7, label: 'Posisjon 8' }
            ];
        }
    }
    
    // Mouse event handlers
    handleMouseDown(event) {
        event.preventDefault();
        this.startDrag(event.target, event.clientX, event.clientY);
        
        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('mouseup', this.handleMouseUp);
    }
    
    handleMouseMove(event) {
        if (this.isDragging) {
            this.updateDrag(event.clientX, event.clientY);
        }
    }
    
    handleMouseUp(event) {
        if (this.isDragging) {
            this.endDrag(event.clientX, event.clientY);
        }
        
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', this.handleMouseUp);
    }
    
    // Touch event handlers
    handleTouchStart(event) {
        event.preventDefault();
        const touch = event.touches[0];
        this.startDrag(event.target, touch.clientX, touch.clientY);
        
        document.addEventListener('touchmove', this.handleTouchMove, { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd);
    }
    
    handleTouchMove(event) {
        event.preventDefault();
        if (this.isDragging) {
            const touch = event.touches[0];
            this.updateDrag(touch.clientX, touch.clientY);
        }
    }
    
    handleTouchEnd(event) {
        if (this.isDragging) {
            const touch = event.changedTouches[0];
            this.endDrag(touch.clientX, touch.clientY);
        }
        
        document.removeEventListener('touchmove', this.handleTouchMove);
        document.removeEventListener('touchend', this.handleTouchEnd);
    }
    
    // Drag logic
    startDrag(vehicleElement, clientX, clientY) {
        this.isDragging = true;
        this.draggedVehicle = vehicleElement;
        
        vehicleElement.classList.add('dragging');
        
        const rect = vehicleElement.getBoundingClientRect();
        const boardRect = document.getElementById('game-board').getBoundingClientRect();
        
        this.dragOffset = {
            x: clientX - rect.left,
            y: clientY - rect.top
        };
        
        this.boardOffset = {
            x: boardRect.left,
            y: boardRect.top
        };
    }
    
    updateDrag(clientX, clientY) {
        if (!this.isDragging || !this.draggedVehicle) return;
        
        const x = clientX - this.boardOffset.x - this.dragOffset.x;
        const y = clientY - this.boardOffset.y - this.dragOffset.y;
        
        this.draggedVehicle.style.left = x + 'px';
        this.draggedVehicle.style.top = y + 'px';
        
        // Check for drop zone hover
        this.checkDropZoneHover(clientX, clientY);
    }
    
    checkDropZoneHover(clientX, clientY) {
        // Remove previous hover effects
        document.querySelectorAll('.drop-zone.drag-over').forEach(zone => {
            zone.classList.remove('drag-over');
        });
        
        // Find drop zone under cursor
        Object.values(this.dropZones).forEach(zone => {
            const rect = zone.element.getBoundingClientRect();
            if (clientX >= rect.left && clientX <= rect.right &&
                clientY >= rect.top && clientY <= rect.bottom) {
                zone.element.classList.add('drag-over');
            }
        });
    }
    
    endDrag(clientX, clientY) {
        if (!this.isDragging || !this.draggedVehicle) return;
        
        const vehicleType = this.draggedVehicle.dataset.vehicleType;
        let droppedOnZone = null;
        
        // Find drop zone under cursor
        Object.entries(this.dropZones).forEach(([zoneId, zone]) => {
            const rect = zone.element.getBoundingClientRect();
            if (clientX >= rect.left && clientX <= rect.right &&
                clientY >= rect.top && clientY <= rect.bottom) {
                droppedOnZone = zoneId;
            }
        });
        
        if (droppedOnZone && !this.dropZones[droppedOnZone].occupied) {
            // Valid drop
            this.placeVehicleInZone(vehicleType, droppedOnZone);
        } else {
            // Invalid drop - return to original position
            this.returnVehicleToStart(vehicleType);
        }
        
        // Clean up
        this.draggedVehicle.classList.remove('dragging');
        document.querySelectorAll('.drop-zone.drag-over').forEach(zone => {
            zone.classList.remove('drag-over');
        });
        
        this.isDragging = false;
        this.draggedVehicle = null;
        
        // Check if all vehicles are placed
        this.checkSubmitAvailability();
    }
    
    placeVehicleInZone(vehicleType, zoneId) {
        const zone = this.dropZones[zoneId];
        const vehicle = this.draggedVehicle;
        
        // Update zone
        zone.occupied = true;
        zone.vehicle = vehicleType;
        zone.element.classList.add('occupied');
        
        // Position vehicle in center of zone
        const zoneRect = zone.element.getBoundingClientRect();
        const boardRect = document.getElementById('game-board').getBoundingClientRect();
        
        const x = zoneRect.left - boardRect.left + (zoneRect.width - 60) / 2;
        const y = zoneRect.top - boardRect.top + (zoneRect.height - 40) / 2;
        
        vehicle.style.left = x + 'px';
        vehicle.style.top = y + 'px';
        
        // Update vehicle position tracking
        this.vehiclePositions[vehicleType] = {
            x: x,
            y: y,
            placed: true,
            zone: zoneId
        };
        
        // Send move action to server
        this.sendVehicleMove(vehicleType, { target_zone: zoneId });
    }
    
    returnVehicleToStart(vehicleType) {
        const startPos = this.gameData.scenario_config.starting_positions[vehicleType];
        
        this.draggedVehicle.style.left = startPos.x + 'px';
        this.draggedVehicle.style.top = startPos.y + 'px';
        
        // Update position tracking
        this.vehiclePositions[vehicleType] = {
            x: startPos.x,
            y: startPos.y,
            placed: false,
            zone: null
        };
    }
    
    async sendVehicleMove(vehicleId, position) {
        try {
            const response = await fetch('/games/rule_puzzle/api/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    action_type: 'move_vehicle',
                    action_data: {
                        vehicle_id: vehicleId,
                        position: position
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update vehicle appearance based on correctness
                const vehicle = document.querySelector(`[data-vehicle-type="${vehicleId}"]`);
                vehicle.classList.remove('placed-correctly', 'placed-incorrectly');
                
                if (data.is_correct) {
                    vehicle.classList.add('placed-correctly');
                } else {
                    vehicle.classList.add('placed-incorrectly');
                }
                
                // Show feedback if needed
                if (data.feedback) {
                    this.showFeedback(data.feedback, data.is_correct);
                }
            }
        } catch (error) {
            console.error('Error sending vehicle move:', error);
        }
    }
    
    showFeedback(message, isCorrect) {
        // Create temporary feedback element
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: ${isCorrect ? '#10b981' : '#ef4444'};
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 1000;
            animation: fadeInOut 2s ease-in-out;
        `;
        feedback.textContent = message;
        
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            document.body.removeChild(feedback);
        }, 2000);
    }
    
    checkSubmitAvailability() {
        const allPlaced = Object.values(this.vehiclePositions).every(pos => pos.placed);
        document.getElementById('submit-btn').disabled = !allPlaced;
    }
    
    async requestHint() {
        try {
            const response = await fetch('/games/rule_puzzle/api/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    action_type: 'request_hint',
                    action_data: {}
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hintsUsed = data.hints_used;
                this.showHint(data.hint);
                this.updateGameStats();
                
                // Update hint button
                document.getElementById('hint-btn').textContent = 
                    `💡 Hint (-5 poeng) (${this.hintsUsed})`;
            }
        } catch (error) {
            console.error('Error requesting hint:', error);
        }
    }
    
    showHint(hintText) {
        const hintContainer = document.getElementById('hint-display');
        const hintTextElement = document.getElementById('hint-text');
        
        hintTextElement.textContent = hintText;
        hintContainer.classList.remove('hidden');
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            hintContainer.classList.add('hidden');
        }, 10000);
    }
    
    async resetScenario() {
        try {
            const response = await fetch('/games/rule_puzzle/api/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    action_type: 'reset_scenario',
                    action_data: {}
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reset all vehicles to starting positions
                Object.entries(this.gameData.scenario_config.starting_positions).forEach(([vehicleType, startPos]) => {
                    const vehicle = document.querySelector(`[data-vehicle-type="${vehicleType}"]`);
                    vehicle.style.left = startPos.x + 'px';
                    vehicle.style.top = startPos.y + 'px';
                    vehicle.classList.remove('placed-correctly', 'placed-incorrectly');
                    
                    this.vehiclePositions[vehicleType] = {
                        x: startPos.x,
                        y: startPos.y,
                        placed: false,
                        zone: null
                    };
                });
                
                // Reset drop zones
                Object.values(this.dropZones).forEach(zone => {
                    zone.occupied = false;
                    zone.vehicle = null;
                    zone.element.classList.remove('occupied');
                });
                
                // Hide hint
                document.getElementById('hint-display').classList.add('hidden');
                
                // Update submit button
                this.checkSubmitAvailability();
            }
        } catch (error) {
            console.error('Error resetting scenario:', error);
        }
    }
    
    async submitSolution() {
        try {
            this.showLoading(true);
            
            // Prepare positions data
            const positions = {};
            Object.entries(this.vehiclePositions).forEach(([vehicleType, pos]) => {
                if (pos.placed) {
                    positions[vehicleType] = { target_zone: pos.zone };
                }
            });
            
            const response = await fetch('/games/rule_puzzle/api/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    positions: positions
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.stopTimer();
                this.showResults(data.result);
            } else {
                throw new Error(data.error || 'Failed to submit solution');
            }
        } catch (error) {
            console.error('Error submitting solution:', error);
            alert('Feil ved innsending av løsning: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    showResults(result) {
        // Update results display
        document.getElementById('final-score').textContent = result.score;
        document.getElementById('xp-earned').textContent = result.xp_earned;
        
        // Show performance data if available
        if (result.performance_data) {
            const perfData = result.performance_data;
            document.getElementById('results-message').textContent = 
                `Du brukte ${perfData.hints_used} hints og gjorde ${perfData.moves_made} trekk.`;
        }
        
        // Show achievements if any
        if (result.achievements_unlocked && result.achievements_unlocked.length > 0) {
            const achievementsContainer = document.getElementById('achievements-container');
            const achievementsList = document.getElementById('achievements-list');
            
            achievementsList.innerHTML = '';
            result.achievements_unlocked.forEach(achievement => {
                const badge = document.createElement('div');
                badge.className = 'achievement-badge';
                badge.textContent = achievement;
                achievementsList.appendChild(badge);
            });
            
            achievementsContainer.classList.remove('hidden');
        }
        
        // Show results screen
        this.showResultsScreen();
    }
    
    startTimer() {
        this.timer = setInterval(() => {
            this.timeRemaining--;
            this.updateGameStats();
            
            if (this.timeRemaining <= 0) {
                this.timeUp();
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    timeUp() {
        this.stopTimer();
        alert('Tiden er ute! Spillet avsluttes.');
        this.submitSolution();
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    updateGameStats() {
        document.getElementById('current-score').textContent = this.currentScore;
        document.getElementById('time-remaining').textContent = this.formatTime(this.timeRemaining);
        document.getElementById('hints-used').textContent = this.hintsUsed;
    }
    
    showSetupScreen() {
        this.hideAllScreens();
        document.getElementById('game-setup').classList.add('active');
        this.stopTimer();
    }
    
    showGameScreen() {
        this.hideAllScreens();
        document.getElementById('game-play').classList.add('active');
    }
    
    showResultsScreen() {
        this.hideAllScreens();
        document.getElementById('game-results').classList.add('active');
    }
    
    hideAllScreens() {
        document.querySelectorAll('.game-screen').forEach(screen => {
            screen.classList.remove('active');
        });
    }
    
    showLoading(show) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }
}

// Add CSS animation for feedback
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
    }
`;
document.head.appendChild(style);

// Export for global use
window.RulePuzzleGame = RulePuzzleGame;