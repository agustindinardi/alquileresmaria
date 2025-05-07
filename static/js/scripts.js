// Funcion para formatear campos de tarjeta de credito
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar esquema de colores verde con negro
    applyGreenBlackColorScheme();
    
    // Formatear numero de tarjeta
    const cardNumberInput = document.getElementById('id_numero_tarjeta');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 16) {
                value = value.slice(0, 16);
            }
            e.target.value = value;
        });
    }
    
    // Formatear fecha de vencimiento
    const expiryDateInput = document.getElementById('id_fecha_vencimiento');
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }
    
    // Formatear codigo de seguridad
    const securityCodeInput = document.getElementById('id_codigo_seguridad');
    if (securityCodeInput) {
        securityCodeInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 4) {
                value = value.slice(0, 4);
            }
            e.target.value = value;
        });
    }
    
    // Validar fechas en formulario de busqueda
    const searchForm = document.querySelector('.search-form form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const startDate = new Date(document.getElementById('id_fecha_inicio').value);
            const endDate = new Date(document.getElementById('id_fecha_fin').value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (startDate < today) {
                alert('La fecha de inicio debe ser posterior a la fecha actual.');
                e.preventDefault();
                return false;
            }
            
            if (endDate < startDate) {
                alert('La fecha de fin debe ser posterior a la fecha de inicio.');
                e.preventDefault();
                return false;
            }
            
            return true;
        });
    }
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-cerrar alertas despues de 5 segundos
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Función para aplicar el esquema de colores verde con negro
function applyGreenBlackColorScheme() {
    // Cambiar los botones btn-primary a btn-success
    document.querySelectorAll('.btn-primary').forEach(button => {
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
    });
    
    // Cambiar los elementos text-primary a text-success
    document.querySelectorAll('.text-primary').forEach(element => {
        element.classList.remove('text-primary');
        element.classList.add('text-success');
    });
    
    // Cambiar los elementos bg-primary a bg-success
    document.querySelectorAll('.bg-primary').forEach(element => {
        element.classList.remove('bg-primary');
        element.classList.add('bg-success');
    });
    
    // Cambiar los bordes y elementos activos
    document.querySelectorAll('.border-primary, .active-primary').forEach(element => {
        element.classList.remove('border-primary', 'active-primary');
        element.classList.add('border-success', 'active-success');
    });
}