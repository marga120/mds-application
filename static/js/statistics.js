/**
 * Statistics page for admin use, shows applicant information
 * 
 * 
 *  
 * 
 */


class StatisticsManager {
    constructor() {
        this.applicants = []
        this.statusOptions = []; // Cache for dynamic status options
        this.init();
    }

    async init() {
        await this.loadStatuses(); // Load statuses first
        this.populateStatusFilter(); // Populate the status filter dropdown
        await this.loadApplicants();
        this.setupEventListeners();
        this.displayOverallStatistics();
        this.displayStatusBreakdown();
        this.displayStatusStatistics(""); // Load "All Statuses" by default
     }

    async loadStatuses() {
        try {
            const response = await fetch('/api/statuses');
            const result = await response.json();
            
            if (result.success && result.statuses) {
                this.statusOptions = result.statuses;
                console.log('Statistics: Loaded statuses:', this.statusOptions);
            } else {
                console.error('Statistics: Failed to load statuses:', result.message);
                this.statusOptions = [];
            }
        } catch (error) {
            console.error('Statistics: Error loading statuses:', error);
            this.statusOptions = [];
        }
    }

    populateStatusFilter() {
        const statusFilter = document.getElementById('statusFilter');
        if (!statusFilter) {
            console.warn('statusFilter dropdown not found');
            return;
        }

        const existingOptions = Array.from(statusFilter.options).map(opt => opt.value);

        this.statusOptions.forEach(status => {
            if (!existingOptions.includes(status.status_name)) {
                const option = document.createElement('option');
                option.value = status.status_name;
                option.textContent = status.status_name;
                statusFilter.appendChild(option);
            }
        });

        console.log('Statistics: Populated statusFilter with', this.statusOptions.length, 'statuses');
    }

    isSubmittedStatus(status) {
        // Match the logic from applicants.js getStatusBadge()
        if (!status || status === "N/A" || status.toLowerCase().includes("unsubmitted")) {
            return false;
        }
        return status.toLowerCase().includes("submitted");
    }

    isUnsubmittedStatus(status) {
        if (!status || status === "N/A" || status.toLowerCase().includes("unsubmitted")) {
            return true;
        }
        const statusLower = status.toLowerCase();
        // If it contains "submitted" but not "unsubmitted", it's submitted
        if (statusLower.includes("submitted")) {
            return false;
        }
        // Everything else is treated as unsubmitted
        return true;
    }                                                            
      displayOverallStatistics() {
      const total = this.applicants.length;

      // Submission Status (using status field logic from applicants.js)
      const submitted = this.applicants.filter(a => this.isSubmittedStatus(a.status)).length;
      const unsubmitted = this.applicants.filter(a => this.isUnsubmittedStatus(a.status)).length;                                                                    
                                                                                                                
      // Domestic vs International                                                                              
      const domestic = this.applicants.filter(a => (a.canadian === "Yes" || a.visa === "PERM")).length;                                
      const international = total - domestic;                                                                   
                                                                                                                
      // Gender Distribution                                                                                    
      const male = this.applicants.filter(a => a.gender === "Male").length;                                     
      const female = this.applicants.filter(a => a.gender === "Female").length;                                 
      const genderNotSpecified = total - male - female;                                                         
                                                                                                                
      // Update counts                                                                                          
      document.getElementById("submittedCount").textContent = submitted;                                        
      document.getElementById("unsubmittedCount").textContent = unsubmitted;                                    
      document.getElementById("domesticCount").textContent = domestic;                                          
      document.getElementById("internationalCount").textContent = international;                                
      document.getElementById("maleCount").textContent = male;                                                  
      document.getElementById("femaleCount").textContent = female;                                              
      document.getElementById("genderNotSpecifiedCount").textContent = genderNotSpecified;                      
                                                                                                                
      // Calculate and update percentages                                                                       
      if (total > 0) {                                                                                          
          const malePercent = ((male / total) * 100).toFixed(1);                                                
          const femalePercent = ((female / total) * 100).toFixed(1);                                            
          const notSpecifiedPercent = ((genderNotSpecified / total) * 100).toFixed(1);                          
                                                                                                                
          document.getElementById("malePercent").textContent = malePercent;                                     
          document.getElementById("femalePercent").textContent = femalePercent;                                 
          document.getElementById("genderNotSpecifiedPercent").textContent = notSpecifiedPercent;               
                                                                                                                
          // Update progress bars                                                                               
          document.getElementById("maleBar").style.width = malePercent + "%";                                   
          document.getElementById("femaleBar").style.width = femalePercent + "%";                               
          document.getElementById("genderNotSpecifiedBar").style.width = notSpecifiedPercent + "%";             
      }                                                                                                         
                                                                                                                
      // Display country distribution
      this.displayCountryDistribution(this.applicants);
  }   

    displayStatusBreakdown() {
        const container = document.getElementById("statusBreakdownList");
        
        if (!container) {
            console.error("Status breakdown container not found");
            return;
        }

        // Use dynamic status options from API
        const canonicalStatusOrder = this.statusOptions.map(s => s.status_name);

        // Initialize all statuses with zero counts
        const statusData = {};
        canonicalStatusOrder.forEach(status => {
            statusData[status] = {
                count: 0,
                totalRating: 0,
                ratedCount: 0
            };
        });

        // Initialize Submitted/Unsubmitted counts
        let submittedCount = 0;
        let unsubmittedCount = 0;
        let submittedTotalRating = 0;
        let submittedRatedCount = 0;
        let unsubmittedTotalRating = 0;
        let unsubmittedRatedCount = 0;

        // Count applicants by review_status and calculate average ratings
        let totalWithStatus = 0;

        this.applicants.forEach(applicant => {
            const status = applicant.review_status || "Not Reviewed";
            
            // Count submitted/unsubmitted
            if (this.isSubmittedStatus(applicant.status)) {
                submittedCount++;
                if (applicant.overall_rating && !isNaN(applicant.overall_rating)) {
                    submittedTotalRating += parseFloat(applicant.overall_rating);
                    submittedRatedCount++;
                }
            } else if (this.isUnsubmittedStatus(applicant.status)) {
                unsubmittedCount++;
                if (applicant.overall_rating && !isNaN(applicant.overall_rating)) {
                    unsubmittedTotalRating += parseFloat(applicant.overall_rating);
                    unsubmittedRatedCount++;
                }
            }
            
            // Only count if the status is in our canonical list
            if (statusData[status]) {
                statusData[status].count++;
                totalWithStatus++;
                
                // Add rating if exists
                if (applicant.overall_rating && !isNaN(applicant.overall_rating)) {
                    statusData[status].totalRating += parseFloat(applicant.overall_rating);
                    statusData[status].ratedCount++;
                }
            }
        });

        // Use the canonical order instead of sorting by count
        const orderedStatuses = canonicalStatusOrder.map(status => [status, statusData[status]]);

        // Calculate submitted/unsubmitted percentages and averages
        const totalApplicants = this.applicants.length;
        const submittedPercentage = totalApplicants > 0 
            ? ((submittedCount / totalApplicants) * 100).toFixed(1) 
            : '0.0';
        const unsubmittedPercentage = totalApplicants > 0 
            ? ((unsubmittedCount / totalApplicants) * 100).toFixed(1) 
            : '0.0';
        const submittedAvgRating = submittedRatedCount > 0 
            ? (submittedTotalRating / submittedRatedCount).toFixed(1)
            : '-';
        const unsubmittedAvgRating = unsubmittedRatedCount > 0 
            ? (unsubmittedTotalRating / unsubmittedRatedCount).toFixed(1)
            : '-';

        // Generate HTML for Submitted/Unsubmitted at the top
        const submittedUnsubmittedHtml = `
            <div class="cursor-pointer hover:bg-blue-50 hover:shadow-sm px-2 py-1.5 rounded transition-all duration-200 status-item" data-status="Submitted Applications">
                <div class="flex justify-between items-center text-xs">
                    <span class="text-gray-700 font-medium truncate" title="Submitted Applications">Submitted Applications</span>
                    <span class="text-gray-600 ml-2 flex-shrink-0">${submittedCount} (${submittedPercentage}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div class="bg-green-500 h-1.5 rounded-full transition-all duration-500" style="width: ${submittedPercentage}%"></div>
                </div>
            </div>
            <div class="cursor-pointer hover:bg-blue-50 hover:shadow-sm px-2 py-1.5 rounded transition-all duration-200 status-item" data-status="Unsubmitted Applications">
                <div class="flex justify-between items-center text-xs">
                    <span class="text-gray-700 font-medium truncate" title="Unsubmitted Applications">Unsubmitted Applications</span>
                    <span class="text-gray-600 ml-2 flex-shrink-0">${unsubmittedCount} (${unsubmittedPercentage}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div class="bg-gray-400 h-1.5 rounded-full transition-all duration-500" style="width: ${unsubmittedPercentage}%"></div>
                </div>
            </div>
        `;

        // Generate HTML for status bars (similar to country bars)
        const reviewStatusHtml = orderedStatuses.map(([status, data]) => {
            const percentage = totalWithStatus > 0 
                ? ((data.count / totalWithStatus) * 100).toFixed(1) 
                : '0.0';
            const avgRating = data.ratedCount > 0 
                ? (data.totalRating / data.ratedCount).toFixed(1)
                : '-';
            const barColor = this.getBarColor(status);
            
            return `
                <div class="cursor-pointer hover:bg-blue-50 hover:shadow-sm px-2 py-1.5 rounded transition-all duration-200 status-item" data-status="${status}">
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-gray-700 font-medium truncate" title="${status}">${status}</span>
                        <span class="text-gray-600 ml-2 flex-shrink-0">${data.count} (${percentage}%)</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                        <div class="h-1.5 rounded-full transition-all duration-500" style="width: ${percentage}%; background-color: ${barColor};"></div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = submittedUnsubmittedHtml + reviewStatusHtml;
        
        // Add click handlers to status items
        this.setupStatusRowClickHandlers();
    }

    setupStatusRowClickHandlers() {
        const statusItems = document.querySelectorAll('.status-item');
        statusItems.forEach(item => {
            item.addEventListener('click', () => {
                const status = item.getAttribute('data-status');
                
                // Set the dropdown value
                const statusFilter = document.getElementById('statusFilter');
                if (statusFilter) {
                    statusFilter.value = status;
                    
                    // Trigger the change event to update the statistics
                    this.displayStatusStatistics(status);
                    
                    // Scroll to the status statistics section
                    const statusStatsSection = document.getElementById('statusStats');
                    if (statusStatsSection) {
                        statusStatsSection.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'start' 
                        });
                    }
                }
            });
        });
    }

    // Helper method to determine status badge color
    getStatusColor(status) {
        const statusConfig = this.statusOptions.find(s => s.status_name === status);
        const color = statusConfig ? statusConfig.badge_color : 'gray';
        
        return `bg-${color}-100 text-${color}-800`;
    }

    // Helper method to determine progress bar color
    getBarColor(status) {
        // Get color from cached status options
        const statusConfig = this.statusOptions.find(s => s.status_name === status);
        const color = statusConfig ? statusConfig.badge_color : 'gray';
        
        const colorMap = {
            'gray': '#6B7280',      // gray-500
            'red': '#EF4444',       // red-500
            'yellow': '#F59E0B',    // yellow-500
            'green': '#10B981',     // green-500
            'blue': '#3B82F6',      // blue-500
            'indigo': '#6366F1',    // indigo-500
            'purple': '#A855F7',    // purple-500
            'pink': '#EC4899',      // pink-500
            'orange': '#F97316',    // orange-500
            'teal': '#14B8A6'       // teal-500
        };
        
        return colorMap[color] || colorMap['gray'];
    }

    async loadApplicants() {
        //Loading applicants grabs the current data.
        //When you fetch from /api/applicants.
        // user_code: "...",
        // submit_date: "2024-01-15" or null,  // date application was submitted
        // canadian: "Yes" or "No",             // domestic vs international
        // gender: "Male" or "Female" or null,  // null/undefined = not specified
        // citizenship_country: "Canada",       // country name
        // status: "Submitted" or "Unsubmitted", etc. // determines submitted/unsubmitted (matches applicants.js logic)
        // // ... other fields 

        try {
            // Get current session ID from SessionStore
            const sessionId = window.SessionStore ? SessionStore.getCurrentSessionId() : null;
            const url = sessionId ? `/api/applicants?session_id=${sessionId}` : "/api/applicants";
            const response = await fetch(url)
            const result = await response.json()

            if(result.success){
                this.applicants = result.applicants || [];
                console.log("Applicants loaded successfully:", this.applicants.length);
                if (this.applicants.length > 0) {
                    //Just some debug code.
                    console.log("Sample applicant:", this.applicants[0]);
                }
            }else{
                console.error("Failed to load the applicants: ", result.message)
                this.applicants = [];
            }


        }catch(error) {
            console.error("Error loading applicants. summary: " + error)
            this.applicants = [];
        }
    }                                                  
                                                                                
    setupEventListeners() {
        const statusFilter = document.getElementById("statusFilter");
        if (statusFilter) {
            statusFilter.addEventListener("change", (e) => {
                const selectedStatus = e.target.value;
                this.displayStatusStatistics(selectedStatus);
            });
        }
    }                                                   
                                                                                
    displayStatusStatistics(status) {
        const statusStatsContainer = document.getElementById("statusStats");
        // Debug logging
        console.log("Selected status:", status);
        console.log("Total applicants:", this.applicants.length);
        console.log("Unique review_status values:", [...new Set(this.applicants.map(a => a.review_status))]);

        // Filter applicants by the selected status (or all if empty)/Submitted || Unsubmitted

        let total;
        let filteredApplicants;
        if(status === "Submitted Applications"){
            // Show only submitted applications (using status field logic from applicants.js)
            filteredApplicants = this.applicants.filter(a => this.isSubmittedStatus(a.status));
            total = filteredApplicants.length;
            console.log("Filtered applicants count (submitted): " , total);
        } else if(status === "Unsubmitted Applications"){
            // Show only unsubmitted applications (using status field logic from applicants.js)
            filteredApplicants = this.applicants.filter(a => this.isUnsubmittedStatus(a.status));
            total = filteredApplicants.length;
            console.log("Filtered applicants count (unsubmitted): " , total);
        } else {
            // Show all applicants or filter by review_status
            filteredApplicants = !status
            ? this.applicants
            : this.applicants.filter(a => a.review_status === status);
            total = filteredApplicants.length;
            console.log("Filtered applicants count:", total);
        }

        // Display title based on selection
        const displayTitle = !status ? "All Statuses" : status;

        // If no applicants with this status
        if (total === 0) {
        statusStatsContainer.innerHTML = `
            <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-xl font-semibold text-gray-800 mb-4">${displayTitle}</h3>
            <p class="text-gray-500 text-center">No applicants with this status</p>
            </div>
        `;
        return;
        }                                                                           
                                                                                    
        // Calculate Domestic vs International                                      
        const domestic = filteredApplicants.filter(a => a.canadian ===              
        "Yes" || a.visa === "PERM").length;                                                                
        const international = total - domestic;                                     
        const domesticPercent = ((domestic / total) * 100).toFixed(1);              
        const internationalPercent = ((international / total) * 100).toFixed(1);    
                                                                                    
        // Calculate Gender Distribution                                            
        const male = filteredApplicants.filter(a => a.gender === "Male").length;    
        const female = filteredApplicants.filter(a => a.gender === "Female").length;
        const genderNotSpecified = total - male - female;                           
        const malePercent = ((male / total) * 100).toFixed(1);                      
        const femalePercent = ((female / total) * 100).toFixed(1);                  
        const notSpecifiedPercent = ((genderNotSpecified / total) * 100).toFixed(1);
                                                                                    
        // Generate country bars HTML                                               
        const countryBarsHTML = this.generateCountryBars(filteredApplicants);       
                                                                                    
        // Generate and inject the complete HTML
        statusStatsContainer.innerHTML = `
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-xl font-semibold text-gray-800 mb-6">
            ${displayTitle}
            <span class="text-gray-500 text-base font-normal">(${total}
        applicants)</span>
            </h3>                                                                   
                                                                                    
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">                     
            <!-- Domestic vs International -->                                    
            <div>                                                                 
                <h4 class="text-md font-semibold text-gray-700 mb-4">Residency      
        Status</h4>                                                                   
                <div class="space-y-3">                                             
                <div>                                                             
                    <div class="flex justify-between text-sm mb-1">                 
                    <span class="text-gray-600">Domestic</span>                   
                    <span class="font-medium text-gray-900">${domestic}           
        (${domesticPercent}%)</span>                                                  
                    </div>                                                          
                    <div class="w-full bg-gray-200 rounded-full h-3">               
                    <div class="bg-blue-500 h-3 rounded-full transition-all       
        duration-500" style="width: ${domesticPercent}%"></div>                       
                    </div>                                                          
                </div>                                                            
                <div>                                                             
                    <div class="flex justify-between text-sm mb-1">                 
                    <span class="text-gray-600">International</span>              
                    <span class="font-medium text-gray-900">${international}      
        (${internationalPercent}%)</span>                                             
                    </div>                                                          
                    <div class="w-full bg-gray-200 rounded-full h-3">
                    <div class="bg-green-600 h-3 rounded-full transition-all
        duration-500" style="width: ${internationalPercent}%"></div>                  
                    </div>                                                          
                </div>                                                            
                </div>                                                              
            </div>                                                                
                                                                                    
            <!-- Gender Distribution -->                                          
            <div>                                                                 
                <h4 class="text-md font-semibold text-gray-700 mb-4">Gender         
        Distribution</h4>                                                             
                <div class="space-y-3">                                             
                <div>                                                             
                    <div class="flex justify-between text-sm mb-1">                 
                    <span class="text-gray-600">Male</span>                       
                    <span class="font-medium text-gray-900">${male}               
        (${malePercent}%)</span>                                                      
                    </div>                                                          
                    <div class="w-full bg-gray-200 rounded-full h-3">               
                    <div class="bg-blue-500 h-3 rounded-full transition-all       
        duration-500" style="width: ${malePercent}%"></div>                           
                    </div>                                                          
                </div>                                                            
                <div>                                                             
                    <div class="flex justify-between text-sm mb-1">                 
                    <span class="text-gray-600">Female</span>                     
                    <span class="font-medium text-gray-900">${female}             
        (${femalePercent}%)</span>                                                    
                    </div>                                                          
                    <div class="w-full bg-gray-200 rounded-full h-3">
                    <div class="bg-pink-500 h-3 rounded-full transition-all
        duration-500" style="width: ${femalePercent}%"></div>                         
                    </div>                                                          
                </div>                                                            
                <div>                                                             
                    <div class="flex justify-between text-sm mb-1">                 
                    <span class="text-gray-600">Not Specified</span>              
                    <span class="font-medium text-gray-900">${genderNotSpecified} 
        (${notSpecifiedPercent}%)</span>                                              
                    </div>                                                          
                    <div class="w-full bg-gray-200 rounded-full h-3">               
                    <div class="bg-gray-400 h-3 rounded-full transition-all       
        uration-500" style="width: ${notSpecifiedPercent}%"></div>                   
                    </div>                                                          
                </div>                                                            
                </div>                                                              
            </div>                                                                
            </div>                                                                  
                                                                                    
            <!-- Top 10 Countries for this status -->                               
            <div class="mt-6">                                                      
            <h4 class="text-md font-semibold text-gray-700 mb-4">Top          
        Countries</h4>                                                                
            <div class="space-y-2 max-h-80 overflow-y-auto">                      
                ${countryBarsHTML}                                                  
            </div>                                                                
            </div>                                                                  
        </div>                                                                    
        `;                                                                          
    }                                              
                                                                                
    displayCountryDistribution(applicants) {                                                                                                                                                    
      const countriesChart = document.getElementById("countriesChart");                                                                                                                       
                                                                                                                                                                                              
      // Count applicants by country                                                                                                                                                          
      const countryCounts = {};                                                                                                                                                               
      applicants.forEach(applicant => {                                                                                                                                                       
          const country = applicant.citizenship_country || "Not Specified";                                                                                                                   
          countryCounts[country] = (countryCounts[country] || 0) + 1;                                                                                                                         
      });                                                                                                                                                                                     
                                                                                                                                                                                              
      // Convert to array and sort by count                                                                                                                                                   
      const sortedCountries = Object.entries(countryCounts)                                                                                                                                   
          .sort((a, b) => b[1] - a[1])                                                                                                                                                        
                                                                                                                                                                                              
      if (sortedCountries.length === 0) {                                                                                                                                                     
          countriesChart.innerHTML = '<div class="text-center text-gray-500 py-4">No data available</div>';                                                                                   
          return;                                                                                                                                                                             
      }                                                                                                                                                                                       
                                                                                                                                                                                              
      const total = applicants.length;                                                                                                                                                        
      const maxCount = sortedCountries[0][1];                                                                                                                                                 
                                                                                                                                                                                              
      // Generate HTML for country bars
      const html = sortedCountries.map(([country, count]) => {
          const percent = ((count / total) * 100).toFixed(1);
          const barWidth = percent; // Bar width should match the actual percentage

          return `
              <div>
                  <div class="flex justify-between text-xs mb-1">
                      <span class="text-gray-700 font-medium truncate" title="${country}">${country}</span>
                      <span class="text-gray-600 ml-2 flex-shrink-0">${count} (${percent}%)</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                      <div class="bg-ubc-blue h-2 rounded-full transition-all duration-500" style="width: ${barWidth}%"></div>
                  </div>
              </div>
          `;
      }).join('');

      countriesChart.innerHTML = html;                                                                                                                                                        
  }                                                                                                                                                                                           
                                                                                                                                                                                              
  generateCountryBars(applicants) {                                                                                                                                                           
      // Count applicants by country                                                                                                                                                          
      const countryCounts = {};                                                                                                                                                               
      applicants.forEach(applicant => {                                                                                                                                                       
          const country = applicant.citizenship_country || "Not Specified";                                                                                                                   
          countryCounts[country] = (countryCounts[country] || 0) + 1;                                                                                                                         
      });                                                                                                                                                                                     
                                                                                                                                                                                              
      // Convert to array and sort by count                                                                                                                                                   
      const sortedCountries = Object.entries(countryCounts)                                                                                                                                   
          .sort((a, b) => b[1] - a[1])                                                                                                                                                        
          .slice(0, 10); // Top 10                                                                                                                                                            
                                                                                                                                                                                              
      if (sortedCountries.length === 0) {                                                                                                                                                     
          return '<div class="text-center text-gray-500 py-4">No data available</div>';                                                                                                       
      }                                                                                                                                                                                       
                                                                                                                                                                                              
      const total = applicants.length;                                                                                                                                                        
      const maxCount = sortedCountries[0][1];                                                                                                                                                 
                                                                                                                                                                                              
      // Generate HTML for country bars
      return sortedCountries.map(([country, count]) => {
          const percent = ((count / total) * 100).toFixed(1);
          const barWidth = percent; // Bar width should match the actual percentage

          return `
              <div>
                  <div class="flex justify-between text-xs mb-1">
                      <span class="text-gray-700 font-medium truncate" title="${country}">${country}</span>
                      <span class="text-gray-600 ml-2 flex-shrink-0">${count} (${percent}%)</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                      <div class="bg-ubc-blue h-2 rounded-full transition-all duration-500" style="width: ${barWidth}%"></div>
                  </div>
              </div>
          `;
      }).join('');                                                                                                                                                                            
    }                                    
  } 