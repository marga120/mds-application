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
        this.init();
    }                                                           
                                                                                
    async init() {
        await this.loadApplicants();
        this.setupEventListeners();
        this.displayOverallStatistics();
        this.displayStatusStatistics(""); // Load "All Statuses" by default
     }                                                            
      displayOverallStatistics() {                                                                                  
      const total = this.applicants.length;                                                                     
                                                                                                                
      // Submission Status                                                                                      
      const submitted = this.applicants.filter(a => a.submit_date).length;                                      
      const unsubmitted = total - submitted;                                                                    
                                                                                                                
      // Domestic vs International                                                                              
      const domestic = this.applicants.filter(a => a.canadian === "Yes").length;                                
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

    async loadApplicants() { 
        //Loading applicants grabs the current data.
        //When you fetch from /api/applicants.
        // user_code: "...",                                                           
        // submit_date: "2024-01-15" or null,  // null means unsubmitted               
        // canadian: "Yes" or "No",             // domestic vs international           
        // gender: "Male" or "Female" or null,  // null/undefined = not specified      
        // citizenship_country: "Canada",       // country name                        
        // status: "Not Reviewed",              // application status                  
        // // ... other fields 

        try {
            const response = await fetch("/api/applicants")
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
            // Show only submitted applications
            filteredApplicants = this.applicants.filter(a => a.submit_date != null);
            total = filteredApplicants.length;
            console.log("Filtered applicants count (submitted): " , total);
        } else if(status === "Unsubmitted Applications"){
            // Show only unsubmitted applications
            filteredApplicants = this.applicants.filter(a => !a.submit_date);
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
        "Yes").length;                                                                
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
                    <div class="bg-purple-500 h-3 rounded-full transition-all     
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